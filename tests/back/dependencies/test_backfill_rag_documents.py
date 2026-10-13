"""Startup conversion of legacy RAG documents into Data documents."""

import json
import pathlib

import pytest
from pydantic import BaseModel
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from DashAI.back.core.enums.status import DocumentStatus
from DashAI.back.dataloaders.classes.dashai_document import (
    DashAIDocument,
    DocumentItem,
    load_document,
)
from DashAI.back.dependencies.database.backfill import backfill_rag_documents
from DashAI.back.dependencies.database.models import (
    Base,
    DataDocument,
    GenerativeProcess,
    GenerativeSession,
    ProcessData,
    RAGChunkSet,
    RAGLegacyDocument,
    RAGSessionDocument,
)
from DashAI.back.types.value_types import Text


class _TextSchema(BaseModel):
    """Parameters the fake text loader accepts."""

    encoding: str = "utf-8"


class _FakeTextLoader:
    """Stand in for a branch 2 document DataLoader: one Text item per file."""

    SCHEMA = _TextSchema
    DEFAULT_PARAMS = {"encoding": "utf-8"}

    def resolve_params(self, params):
        """Merge ``params`` over the defaults and validate them.

        Parameters
        ----------
        params : dict or None
            Loader parameters.

        Returns
        -------
        dict
            Every schema field with its value.
        """
        return self.SCHEMA.model_validate(
            {**self.DEFAULT_PARAMS, **(params or {})}
        ).model_dump()

    def load_document(self, file_path, params):
        """Return the file text as a one page document.

        Parameters
        ----------
        file_path : str
            Path of the file to parse.
        params : dict
            Loader parameters.

        Returns
        -------
        DashAIDocument
            The parsed document.
        """
        text = pathlib.Path(file_path).read_text(encoding=params["encoding"])
        return DashAIDocument.from_items([DocumentItem(Text, text, page=1)])


REGISTRY = {
    "PlainTextDocumentDataLoader": {"class": _FakeTextLoader},
    "PdfPlumberDocumentDataLoader": {"class": _FakeTextLoader},
}


@pytest.fixture
def factory(tmp_path):
    """Yield a session factory over a fresh database file."""
    engine = create_engine(f"sqlite:///{tmp_path / 'backfill.db'}")
    Base.metadata.create_all(engine)
    yield sessionmaker(bind=engine)
    engine.dispose()


@pytest.fixture
def documents_root(tmp_path):
    """Return a documents folder with an empty ``blobs`` directory."""
    root = tmp_path / "documents"
    (root / "blobs").mkdir(parents=True)
    return root


def _blob(root, name, text) -> str:
    """Write a legacy blob and return its path.

    Parameters
    ----------
    root : pathlib.Path
        Documents folder.
    name : str
        Blob file name.
    text : str
        Blob content.

    Returns
    -------
    str
        Path of the blob.
    """
    path = root / "blobs" / name
    path.write_text(text, encoding="utf-8")
    return str(path)


def _session(db, name, documents) -> int:
    """Insert a RAG session whose parameters list legacy document ids.

    Parameters
    ----------
    db : Session
        Database session.
    name : str
        Session name.
    documents : list of int
        Legacy ids stored in ``parameters["documents"]``.

    Returns
    -------
    int
        The session id.
    """
    session = GenerativeSession(
        name=name,
        task_name="RAGTask",
        model_name="RAGPipeline",
        parameters={"documents": documents},
    )
    db.add(session)
    db.commit()
    return session.id


def _stage(
    db, legacy_id, session_id, file_path, component="PlainTextExtractor", params=None
):
    """Insert a staged legacy document.

    Parameters
    ----------
    db : Session
        Database session.
    legacy_id : int
        Legacy document id.
    session_id : int
        Owning session.
    file_path : str
        Legacy blob path.
    component : str
        Extractor component the row was parsed with.
    params : dict, optional
        Extractor parameters.
    """
    db.add(
        RAGLegacyDocument(
            id=legacy_id,
            session_id=session_id,
            file_name="notes.txt",
            file_type="txt",
            file_path=file_path,
            file_hash="h1",
            extractor_component=component,
            extractor_params=params or {},
        )
    )
    db.commit()


def test_a_staged_document_becomes_a_linked_data_document(factory, documents_root):
    with factory() as db:
        session_id = _session(db, "legacy_one", [5])
        _stage(db, 5, session_id, _blob(documents_root, "h1", "hello world"))

    backfill_rag_documents(factory, REGISTRY, documents_root)

    with factory() as db:
        document = db.query(DataDocument).one()
        session = db.get(GenerativeSession, session_id)
        assert document.status == DocumentStatus.FINISHED
        assert document.dataloader == "PlainTextDocumentDataLoader"
        content = load_document(str(pathlib.Path(document.file_path) / "document"))
        assert content[Text] == ["hello world"]
        assert [link.data_document_id for link in session.document_links] == [
            document.id
        ]
        assert session.parameters["documents"] == [document.id]
        assert session.needs_reindex is True
        assert db.query(RAGLegacyDocument).count() == 0
    assert not (documents_root / "blobs").exists()


def test_the_same_parse_in_two_sessions_is_one_data_document(factory, documents_root):
    with factory() as db:
        first = _session(db, "legacy_a", [5])
        second = _session(db, "legacy_b", [6])
        blob = _blob(documents_root, "h1", "shared text")
        _stage(db, 5, first, blob)
        _stage(db, 6, second, blob)

    backfill_rag_documents(factory, REGISTRY, documents_root)
    backfill_rag_documents(factory, REGISTRY, documents_root)

    with factory() as db:
        document = db.query(DataDocument).one()
        assert (
            db.query(RAGSessionDocument).filter_by(data_document_id=document.id).count()
            == 2
        )


def test_the_extractor_picks_the_loader_and_its_params(factory, documents_root):
    with factory() as db:
        session_id = _session(db, "legacy_params", [5])
        _stage(
            db,
            5,
            session_id,
            _blob(documents_root, "h1", "x"),
            component="PdfPlumberExtractor",
            params={"encoding": "utf-8", "layout": True},
        )

    backfill_rag_documents(factory, REGISTRY, documents_root)

    with factory() as db:
        document = db.query(DataDocument).one()
        assert document.dataloader == "PdfPlumberDocumentDataLoader"
        assert document.dataloader_params == {"encoding": "utf-8"}


def test_a_missing_file_is_recorded_and_not_retried(factory, documents_root):
    with factory() as db:
        session_id = _session(db, "legacy_missing", [5])
        _stage(db, 5, session_id, str(documents_root / "blobs" / "gone"))

    backfill_rag_documents(factory, REGISTRY, documents_root)

    with factory() as db:
        assert db.get(RAGLegacyDocument, 5).error
        assert db.query(DataDocument).count() == 0
        assert db.get(GenerativeSession, session_id).parameters["documents"] == []


def test_chat_citations_follow_the_new_ids(factory, documents_root):
    with factory() as db:
        session_id = _session(db, "legacy_chat", [5])
        _stage(db, 5, session_id, _blob(documents_root, "h1", "cited text"))
        process = GenerativeProcess(session_id=session_id)
        db.add(process)
        db.flush()
        reference = {"document_id": 5, "document_name": "notes.txt", "text": "c"}
        db.add(
            ProcessData(
                process_id=process.id,
                data=json.dumps({"5_0": reference}),
                data_type="Dict",
                is_input=False,
            )
        )
        db.commit()

    backfill_rag_documents(factory, REGISTRY, documents_root)

    with factory() as db:
        document = db.query(DataDocument).one()
        stored = db.query(ProcessData).filter_by(data_type="Dict").one()
        assert json.loads(stored.data)["5_0"]["document_id"] == document.id


def test_unowned_chunk_sets_are_removed(factory, documents_root):
    with factory() as db:
        owner = _session(db, "legacy_owner", [])
        db.add_all(
            [
                RAGChunkSet(signature="legacy", parameters={}),
                RAGChunkSet(signature="owned", parameters={}, session_id=owner),
            ]
        )
        db.commit()

    backfill_rag_documents(factory, REGISTRY, documents_root)

    with factory() as db:
        assert [c.signature for c in db.query(RAGChunkSet).all()] == ["owned"]
