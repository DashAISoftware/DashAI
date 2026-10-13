"""The link table between RAG sessions and Data documents."""

import pytest
from sqlalchemy.exc import IntegrityError

from DashAI.back.dependencies.database.models import RAGSessionDocument
from tests.back.RAG.conftest import _insert_data_document, _insert_rag_session


def test_a_session_links_a_document_once(orm_db, tmp_path):
    session = _insert_rag_session(orm_db, "link_once")
    document = _insert_data_document(orm_db, tmp_path, "a.txt", ["alpha"])
    orm_db.add(RAGSessionDocument(session_id=session.id, data_document_id=document.id))
    orm_db.commit()

    orm_db.add(RAGSessionDocument(session_id=session.id, data_document_id=document.id))
    with pytest.raises(IntegrityError):
        orm_db.commit()


def test_two_sessions_share_a_document(orm_db, tmp_path):
    first = _insert_rag_session(orm_db, "share_a")
    second = _insert_rag_session(orm_db, "share_b")
    document = _insert_data_document(orm_db, tmp_path, "b.txt", ["beta"])
    orm_db.add_all(
        [
            RAGSessionDocument(session_id=first.id, data_document_id=document.id),
            RAGSessionDocument(session_id=second.id, data_document_id=document.id),
        ]
    )
    orm_db.commit()

    assert [link.data_document_id for link in first.document_links] == [document.id]
    assert [link.data_document_id for link in second.document_links] == [document.id]
    assert first.needs_reindex is False
