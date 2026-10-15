"""Chunk sets are stored as chunked documents under the RAG folder."""

from pathlib import Path

from DashAI.back.dataloaders.classes.dashai_document import load_document
from DashAI.back.dependencies.database.models import (
    RAGChunkingModel,
    RAGChunkSetDocument,
)
from DashAI.back.models.RAG.chunking_models.character_chunk_model import (
    CharacterChunkModel,
)
from DashAI.back.services.RAG.chunking_service import (
    ChunkingService,
    chunk_document_dir,
)
from DashAI.back.services.RAG.document_service import DocumentService
from DashAI.back.types.value_types import Text
from tests.back.RAG.conftest import _insert_data_document, _insert_rag_session

PARAMS = {"chunk_size": 30, "chunk_overlap": 5}
CONFIG = {"chunking_model": {"component": "CharacterChunkModel", "params": PARAMS}}
REGISTRY = {"CharacterChunkModel": {"class": CharacterChunkModel}}


def _chunk(orm_db, tmp_path, session_name, pages_by_name):
    session = _insert_rag_session(orm_db, session_name)
    ids = [
        _insert_data_document(orm_db, tmp_path / "docs", name, pages).id
        for name, pages in pages_by_name.items()
    ]
    service = ChunkingService(orm_db, REGISTRY, str(tmp_path / "rag"))
    chunk_set = service.get_or_create_chunk_set(session.id, ids, CONFIG)
    sources = DocumentService(orm_db).load(ids)
    record_id, result = service.create(
        sources, chunk_set.id, "CharacterChunkModel", PARAMS
    )
    return service, chunk_set, record_id, result


def _link(orm_db, chunk_set_id):
    return orm_db.query(RAGChunkSetDocument).filter_by(chunk_set_id=chunk_set_id)


def test_chunks_are_written_as_a_document_per_source(orm_db, tmp_path):
    _, chunk_set, _, result = _chunk(
        orm_db,
        tmp_path,
        "store_a",
        {"a.txt": ["First page text here.", "Second page text here."]},
    )

    link = _link(orm_db, chunk_set.id).one()
    assert Path(link.path) == chunk_document_dir(
        tmp_path / "rag", chunk_set.id, link.document_id
    )
    stored = load_document(link.path)
    assert stored.count(Text) == link.n_chunks
    assert link.n_chunks > 1
    assert stored.metadata["source_document_id"] == link.document_id
    assert stored.metadata["chunker"] == "CharacterChunkModel"
    chunks = result.chunks[link.document_id]
    assert [chunk.text for chunk in chunks.values()] == stored[Text]
    assert chunks[0].page == 1
    assert chunks[len(chunks) - 1].page == 2


def test_chunk_ids_are_ordinals_across_documents(orm_db, tmp_path):
    _, _, _, result = _chunk(
        orm_db,
        tmp_path,
        "store_b",
        {
            "x.txt": ["one two three four five six seven eight"],
            "y.txt": ["nine ten eleven twelve thirteen fourteen"],
        },
    )

    ordered = [
        chunk
        for document_id in sorted(result.chunks)
        for _, chunk in sorted(result.chunks[document_id].items())
    ]
    assert [chunk.id for chunk in ordered] == list(range(len(ordered)))


def test_a_second_run_reuses_the_stored_chunks(orm_db, tmp_path):
    service, chunk_set, record_id, first = _chunk(
        orm_db, tmp_path, "store_c", {"c.txt": ["Some text to split in pieces."]}
    )
    link = _link(orm_db, chunk_set.id).one()
    stamp = (Path(link.path) / "document.json").stat().st_mtime_ns

    sources = DocumentService(orm_db).load([link.document_id])
    again_id, again = service.create(
        sources, chunk_set.id, "CharacterChunkModel", PARAMS
    )

    assert again_id == record_id
    assert (Path(link.path) / "document.json").stat().st_mtime_ns == stamp
    assert {
        doc: [chunk.text for chunk in chunks.values()]
        for doc, chunks in again.chunks.items()
    } == {
        doc: [chunk.text for chunk in chunks.values()]
        for doc, chunks in first.chunks.items()
    }
    assert orm_db.query(RAGChunkingModel).count() == 1


def test_a_cached_chunker_still_chunks_a_new_chunk_set(orm_db, tmp_path):
    _chunk(orm_db, tmp_path, "cache_a", {"p.txt": ["Text of the first set."]})

    _, second_set, _, result = _chunk(
        orm_db, tmp_path, "cache_b", {"q.txt": ["Text of the second set."]}
    )

    assert result.chunks
    assert all(result.chunks.values())
    assert _link(orm_db, second_set.id).one().n_chunks > 0


def test_a_document_without_text_stores_no_chunks(orm_db, tmp_path):
    _, chunk_set, _, result = _chunk(orm_db, tmp_path, "empty", {"e.txt": [""]})

    link = _link(orm_db, chunk_set.id).one()
    assert link.n_chunks == 0
    assert Path(link.path).is_dir()
    assert result.chunks[link.document_id] == {}
