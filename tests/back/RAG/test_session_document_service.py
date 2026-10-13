"""Attaching and detaching Data documents at the service level."""

import uuid

import pytest

from DashAI.back.core.enums.status import DocumentStatus
from DashAI.back.dependencies.database.models import (
    DataDocument,
    GenerativeSession,
    GenerativeSessionParameterHistory,
    RAGChunkSet,
)
from DashAI.back.services.RAG.session_document_service import (
    DocumentNotReadyError,
    SessionDocumentService,
)
from tests.back.RAG.conftest import _insert_data_document, _insert_rag_session


def _owned_chunk_set(db, session_id) -> int:
    """Insert an empty chunk set owned by a session.

    Parameters
    ----------
    db : Session
        Database session to write with.
    session_id : int
        Owning session.

    Returns
    -------
    int
        The chunk set id.
    """
    chunk_set = RAGChunkSet(
        signature=uuid.uuid4().hex, parameters={}, session_id=session_id
    )
    db.add(chunk_set)
    db.commit()
    return chunk_set.id


def test_attach_links_mirrors_and_historizes(orm_db, tmp_path):
    session = _insert_rag_session(orm_db, "svc_attach")
    document = _insert_data_document(orm_db, tmp_path, "a.txt", ["a"])
    service = SessionDocumentService(orm_db)

    attached = service.attach(session.id, [document.id, document.id])
    service.attach(session.id, [document.id])

    assert [d.id for d in attached] == [document.id]
    assert service.linked_document_ids(session.id) == [document.id]
    assert orm_db.get(GenerativeSession, session.id).parameters["documents"] == [
        document.id
    ]
    assert (
        orm_db.query(GenerativeSessionParameterHistory)
        .filter_by(session_id=session.id)
        .count()
        == 1
    )


def test_attach_refuses_missing_unready_and_non_rag(orm_db, tmp_path):
    session = _insert_rag_session(orm_db, "svc_refuse")
    pending = _insert_data_document(
        orm_db, tmp_path, "p.txt", ["p"], status=DocumentStatus.STARTED
    )
    other = GenerativeSession(
        name="svc_llm",
        task_name="TextToTextGenerationTask",
        model_name="QwenModel",
        parameters={},
    )
    orm_db.add(other)
    orm_db.commit()
    service = SessionDocumentService(orm_db)

    with pytest.raises(LookupError):
        service.attach(session.id, [987654])
    with pytest.raises(DocumentNotReadyError):
        service.attach(session.id, [pending.id])
    with pytest.raises(ValueError, match="only RAG sessions"):
        service.attach(other.id, [pending.id])


def test_changing_the_documents_discards_only_this_sessions_indexes(orm_db, tmp_path):
    first = _insert_rag_session(orm_db, "svc_first")
    second = _insert_rag_session(orm_db, "svc_second")
    document = _insert_data_document(orm_db, tmp_path, "s.txt", ["s"])
    extra = _insert_data_document(orm_db, tmp_path, "e.txt", ["e"])
    service = SessionDocumentService(orm_db)
    service.attach(first.id, [document.id])
    service.attach(second.id, [document.id])
    first_set = _owned_chunk_set(orm_db, first.id)
    second_set = _owned_chunk_set(orm_db, second.id)

    service.attach(first.id, [extra.id])
    assert orm_db.get(RAGChunkSet, first_set) is None
    assert orm_db.get(RAGChunkSet, second_set) is not None

    later_set = _owned_chunk_set(orm_db, first.id)
    service.detach(first.id, document.id)
    assert orm_db.get(RAGChunkSet, later_set) is None
    assert orm_db.get(RAGChunkSet, second_set) is not None
    assert orm_db.get(DataDocument, document.id) is not None
    assert service.linked_document_ids(first.id) == [extra.id]
    assert [s.id for s in service.sessions_using(document.id)] == [second.id]


def test_detaching_a_document_the_session_does_not_hold_is_refused(orm_db, tmp_path):
    session = _insert_rag_session(orm_db, "svc_detach_missing")
    document = _insert_data_document(orm_db, tmp_path, "d.txt", ["d"])

    with pytest.raises(LookupError):
        SessionDocumentService(orm_db).detach(session.id, document.id)
