"""Fixtures for RAG API integration tests.

Shares the same client fixture as the api/ tests so that generative
session / prompt endpoints are available.

Note on ``DocumentService(db)``: the constructor accepts an optional
``registry`` (defaults to ``None``).  Extractors can only be resolved when a
registry is supplied, so existing callers that construct
``DocumentService(db)`` without a registry keep working unchanged (their
hydrated documents simply have no extractor).  Use
``DocumentService(db, client.app.container["component_registry"])`` whenever
extractor resolution is required.
"""

import os
import shutil
import tempfile
import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from DashAI.back.app import create_app
from DashAI.back.dependencies.database.models import (
    Document,
    GenerativeSession,
    GenerativeSessionParameterHistory,
    RAGExtractor,
)
from DashAI.back.dependencies.job_queues.huey_job_queue import HueyJobQueue

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


def _add_document_to_session(
    client: TestClient, session_id: int, suffix: str = ""
) -> int:
    """Attach a minimal test document to a RAG session and return its ID.

    Documents belong to exactly one session, so a document cannot exist before
    the session that owns it. The session's ``parameters["documents"]`` list is
    updated in the same transaction, mirroring what ``DocumentService.upload``
    does, so the pipeline and the index status see the document too.

    Uses ``tempfile.gettempdir()`` for a cross-platform temporary path.
    """
    session_factory = client.app.container["session_factory"]
    with session_factory() as db:
        extractor = RAGExtractor(component_name="PlainTextExtractor", params={})
        db.add(extractor)
        db.flush()
        doc = Document(
            session_id=session_id,
            file_name=f"test_doc{suffix}.txt",
            file_type="txt",
            file_path=os.path.join(tempfile.gettempdir(), f"test_doc{suffix}.txt"),
            file_hash=f"test_hash_123_{suffix}" if suffix else "test_hash_123",
            extractor_id=extractor.id,
        )
        db.add(doc)
        db.flush()

        session = db.get(GenerativeSession, session_id)
        parameters = dict(session.parameters or {})
        parameters["documents"] = [*(parameters.get("documents") or []), doc.id]
        session.parameters = parameters
        # DocumentService.upload also historizes the change, and the index
        # status reads that history to tell "stale" from "never indexed".
        db.add(
            GenerativeSessionParameterHistory(
                session_id=session_id, parameters=parameters
            )
        )

        db.commit()
        db.refresh(doc)
        return doc.id


def _create_test_document(client: TestClient, suffix: str = "") -> int:
    """Create a test document in a throwaway session and return its ID.

    A document cannot exist without an owning session, but service-level tests
    only need a document that exists -- they never assert which session holds
    it. This provisions a minimal session to hang it off. Use
    ``_add_document_to_session`` when the owning session matters.
    """
    session_factory = client.app.container["session_factory"]
    with session_factory() as db:
        holder = GenerativeSession(
            name=f"doc_holder{suffix}",
            task_name="RAGTask",
            model_name="RAGPipeline",
            parameters={"documents": []},
        )
        db.add(holder)
        db.commit()
        session_id = holder.id
    return _add_document_to_session(client, session_id, suffix=suffix)


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
