"""Chunks keep the page they start in, from chunking to the database."""

import pytest

from DashAI.back.core.enums.status import DocumentStatus
from DashAI.back.dependencies.database.models import Chunk as ChunkRow
from DashAI.back.models.RAG.chunking_models.character_chunk_model import (
    CharacterChunkModel,
)
from DashAI.back.models.RAG.documents import RAGDocument, TextSegment
from DashAI.back.services.RAG.chunking_service import ChunkingService
from DashAI.back.services.RAG.document_service import DocumentService
from tests.back.RAG.conftest import _insert_data_document, _insert_rag_session

PAGE_ONE = "alpha beta gamma delta"
PAGE_TWO = "epsilon zeta eta theta"
PARAMS = {"chunk_size": 12, "chunk_overlap": 2}
CONFIG = {"chunking_model": {"component": "CharacterChunkModel", "params": PARAMS}}
EXPECTED_PAGES = [1, 1, 1, 2, 2]


def test_chunks_record_the_page_they_start_in():
    document = RAGDocument(
        id=7,
        name="two.pdf",
        segments=[TextSegment(PAGE_ONE, 1), TextSegment(PAGE_TWO, 2)],
    )
    model = CharacterChunkModel(**PARAMS, documents={7: document})

    chunks = model.get_chunks()[7]

    assert [chunks[i].page for i in sorted(chunks)] == EXPECTED_PAGES


def test_chunk_pages_survive_persistence(orm_db, tmp_path):
    session = _insert_rag_session(orm_db, "pages")
    record = _insert_data_document(orm_db, tmp_path, "two.pdf", [PAGE_ONE, PAGE_TWO])
    documents = DocumentService(orm_db).load([record.id])
    chunking = ChunkingService(
        orm_db, {"CharacterChunkModel": {"class": CharacterChunkModel}}
    )
    chunk_set = chunking.get_or_create_chunk_set(session.id, [record.id], CONFIG)

    chunking.create(documents, chunk_set.id, "CharacterChunkModel", PARAMS)
    rows = (
        orm_db.query(ChunkRow)
        .filter_by(chunk_set_id=chunk_set.id)
        .order_by(ChunkRow.chunk_index)
        .all()
    )
    _, cached = chunking.create(documents, chunk_set.id, "CharacterChunkModel", PARAMS)
    rebuilt = cached.chunks[record.id]

    assert [row.chunk_metadata["page"] for row in rows] == EXPECTED_PAGES
    assert [rebuilt[i].page for i in sorted(rebuilt)] == EXPECTED_PAGES


def test_loading_a_document_still_being_parsed_is_refused(orm_db, tmp_path):
    record = _insert_data_document(
        orm_db, tmp_path, "pending.txt", ["x"], status=DocumentStatus.STARTED
    )

    with pytest.raises(ValueError, match="not ready"):
        DocumentService(orm_db).load([record.id])


def test_loading_a_missing_document_is_refused(orm_db):
    with pytest.raises(ValueError, match="not found"):
        DocumentService(orm_db).load([424242])
