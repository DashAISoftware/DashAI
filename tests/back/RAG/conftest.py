"""Fixtures for the RAG tests.

An app client, an in memory database and Data documents.
"""

import os
import shutil
import tempfile
import time
import uuid
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from DashAI.back.app import create_app
from DashAI.back.core.enums.status import DocumentStatus
from DashAI.back.dataloaders.classes.dashai_document import (
    DashAIDocument,
    DocumentItem,
    save_document,
)
from DashAI.back.dependencies.database.models import (
    Base,
    DataDocument,
    GenerativeSession,
    GenerativeSessionParameterHistory,
    RAGSessionDocument,
)
from DashAI.back.dependencies.job_queues.huey_job_queue import HueyJobQueue
from DashAI.back.types.value_types import Text

# Shared constants for RAG E2E tests
RAG_E2E_DOC_TEXT = (
    "DashAI is a graphical toolbox for training, evaluating and deploying "
    "machine learning models. It provides a complete graphical interface "
    "that allows users to compare and use different machine learning "
    "algorithms without writing code. " * 50
)


def bm25_retriever_params() -> dict:
    """Return standard BM25 retriever parameters for tests."""
    return {
        "BM25Vectorizer": {
            "component": "BM25VectorizerModel",
            "params": {
                "strip_accents": None,
                "lowercase": True,
                "stop_words": None,
                "max_df": 1.0,
                "min_df": 0.0,
                "max_features": None,
            },
        },
        "k1": 1.5,
        "b": 0.75,
        "delta": 0.0,
        "similarity_function": "cosine",
        "top_k": 5,
    }


def write_test_doc_file(suffix: str, text: str) -> str:
    """Write test text to a temp file and return its path."""
    path = os.path.join(tempfile.gettempdir(), f"test_doc{suffix}.txt")
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    return path


def _create_data_document(
    client: TestClient,
    text: str = RAG_E2E_DOC_TEXT,
    name: str = None,
    pages: list = None,
) -> int:
    """Create a finished Data document in the app under test.

    Parameters
    ----------
    client : TestClient
        Client of the app under test.
    text : str
        Text of the single page, ignored when ``pages`` is given.
    name : str, optional
        Unique document name; a random one when omitted.
    pages : list of str, optional
        Text of each page.

    Returns
    -------
    int
        The ``data_document`` id.
    """
    config = client.app.container["config"]
    session_factory = client.app.container["session_factory"]
    with session_factory() as db:
        record = _insert_data_document(
            db,
            Path(config["DOCUMENTS_PATH"]),
            name or f"doc_{uuid.uuid4().hex[:8]}.txt",
            pages if pages is not None else [text],
        )
        return record.id


def _add_document_to_session(
    client: TestClient,
    session_id: int,
    suffix: str = "",
    text: str = RAG_E2E_DOC_TEXT,
) -> int:
    """Attach a new Data document to a RAG session and return its id.

    Links it and mirrors the link into ``parameters["documents"]`` with a
    history entry, as ``SessionDocumentService.attach`` does, so the pipeline
    and the index status see it.

    Parameters
    ----------
    client : TestClient
        Client of the app under test.
    session_id : int
        The RAG session.
    suffix : str
        Part of the document name.
    text : str
        Document text.

    Returns
    -------
    int
        The ``data_document`` id.
    """
    document_id = _create_data_document(
        client, text=text, name=f"test_doc{suffix}_{uuid.uuid4().hex[:6]}.txt"
    )
    session_factory = client.app.container["session_factory"]
    with session_factory() as db:
        db.add(RAGSessionDocument(session_id=session_id, data_document_id=document_id))
        session = db.get(GenerativeSession, session_id)
        parameters = dict(session.parameters or {})
        parameters["documents"] = [*(parameters.get("documents") or []), document_id]
        session.parameters = parameters
        db.add(
            GenerativeSessionParameterHistory(
                session_id=session_id, parameters=parameters
            )
        )
        db.commit()
    return document_id


def _create_test_document(
    client: TestClient, suffix: str = "", text: str = RAG_E2E_DOC_TEXT
) -> int:
    """Create a Data document attached to no session.

    Parameters
    ----------
    client : TestClient
        Client of the app under test.
    suffix : str
        Part of the document name.
    text : str
        Document text.

    Returns
    -------
    int
        The ``data_document`` id.
    """
    return _create_data_document(
        client, text=text, name=f"test_doc{suffix}_{uuid.uuid4().hex[:6]}.txt"
    )


def _create_rag_session(client: TestClient, payload: dict) -> int:
    """Create a RAG session and return its ID, failing loudly on a bad payload.

    ``documents`` is stripped from the payload: a session is always created
    empty and gains its documents afterwards, so sending them is rejected.
    """
    body = {**payload, "parameters": dict(payload.get("parameters") or {})}
    body["parameters"].pop("documents", None)
    response = client.post("/api/v1/generative-session/", json=body)
    assert response.status_code == 201, response.text
    return response.json()["id"]


def _create_session_with_document(
    client: TestClient, payload: dict, suffix: str = ""
) -> "tuple[int, int]":
    """Create a RAG session, attach one document, and return both IDs."""
    session_id = _create_rag_session(client, payload)
    document_id = _add_document_to_session(client, session_id, suffix=suffix)
    return session_id, document_id


def _mark_download_required_components_present(app) -> None:
    """Create each download-required component's repo folder so the download
    gate (reconciled against the filesystem) treats it as available without
    fetching weights.

    Every GGUF text-generation checkpoint (Llama32_1BInstruct, Qwen25_15BInstruct,
    etc.) requires a download, so session creation would otherwise be rejected
    with HTTP 409. Following the pattern in ``tests/back/api/conftest.py``, an
    empty file inside ``<COMPONENT_PATH>/<ClassName>/<repo-leaf>`` is enough for
    ``HFDownloadableMixin.is_downloaded`` to report the component as present.
    """
    registry = app.container["component_registry"]
    components_root = Path(app.container["config"]["COMPONENT_PATH"])

    for component_dict in registry.get_components_by_types():
        component_class = component_dict["class"]
        if not getattr(component_class, "REQUIRES_DOWNLOAD", False):
            continue
        try:
            repos = component_class.hf_repos()
        except Exception:
            continue
        for repo_id, *_ in repos:
            repo_dir = (
                components_root / component_class.__name__ / repo_id.split("/")[-1]
            )
            repo_dir.mkdir(parents=True, exist_ok=True)
            (repo_dir / "config.json").write_text("{}", encoding="utf-8")


def remove_dir_with_retry(directory, max_attempts=5, sleep_seconds=1):
    for attempt in range(max_attempts):
        try:
            shutil.rmtree(directory)
            break
        except PermissionError as e:
            print(f"Attempt {attempt + 1} failed with error: {e}")
            time.sleep(sleep_seconds)
    else:
        print(f"Failed to remove directory after {max_attempts} attempts.")


@pytest.fixture
def orm_db():
    """Yield a session on an isolated in memory database with every table."""
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    db = sessionmaker(bind=engine)()
    yield db
    db.close()
    engine.dispose()


def _insert_rag_session(db, name: str) -> GenerativeSession:
    """Insert an empty RAG session.

    Parameters
    ----------
    db : Session
        Database session to write with.
    name : str
        Unique session name.

    Returns
    -------
    GenerativeSession
        The committed session.
    """
    session = GenerativeSession(
        name=name,
        task_name="RAGTask",
        model_name="RAGPipeline",
        parameters={"documents": []},
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def _insert_data_document(
    db,
    root: Path,
    name: str,
    pages: list,
    status: DocumentStatus = DocumentStatus.FINISHED,
) -> DataDocument:
    """Write a parsed text document under ``root`` and insert its row.

    Parameters
    ----------
    db : Session
        Database session to write with.
    root : Path
        Directory receiving the ``<uuid>/document`` folder.
    name : str
        Unique document name, also used as file name.
    pages : list of str
        Text of each page, page numbers start at 1.
    status : DocumentStatus
        Parsing status stored on the row.

    Returns
    -------
    DataDocument
        The committed document.
    """
    folder = Path(root) / uuid.uuid4().hex
    items = [
        DocumentItem(Text, text, page=index + 1) for index, text in enumerate(pages)
    ]
    save_document(DashAIDocument.from_items(items), str(folder / "document"))
    record = DataDocument(
        name=name,
        file_name=name,
        file_type=Path(name).suffix.lstrip(".") or "txt",
        file_hash=folder.name,
        file_path=str(folder),
        dataloader="PlainTextDocumentDataLoader",
        dataloader_params={},
        content_counts={"Text": len(items)},
        total_pages=len(items),
        status=status,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@pytest.fixture(scope="module")
def client(test_path: Path):
    app = create_app(
        local_path=test_path,
        logging_level="ERROR",
    )

    job_queue = app.container._services.get("job_queue")
    if job_queue and isinstance(job_queue, HueyJobQueue):
        job_queue.set_test_mode(True)

    _mark_download_required_components_present(app)

    test_client = TestClient(app)
    yield test_client

    if job_queue and isinstance(job_queue, HueyJobQueue):
        job_queue.set_test_mode(False)

    app.container._services["engine"].dispose()
    remove_dir_with_retry(app.container._services["config"]["LOCAL_PATH"])


def _create_holder_session(client: TestClient, name: str) -> int:
    """Create an empty RAG session through the app's database.

    Parameters
    ----------
    client : TestClient
        Client of the app under test.
    name : str
        Unique session name.

    Returns
    -------
    int
        The session id.
    """
    session_factory = client.app.container["session_factory"]
    with session_factory() as db:
        return _insert_rag_session(db, name).id
