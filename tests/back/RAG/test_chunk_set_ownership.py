"""Two sessions never share a chunk set, whatever documents they use."""

from DashAI.back.services.RAG.chunking_service import ChunkingService
from tests.back.RAG.conftest import _insert_data_document, _insert_rag_session

CONFIG = {
    "chunking_model": {
        "component": "CharacterChunkModel",
        "params": {"chunk_size": 200, "chunk_overlap": 20},
    }
}


def test_the_signature_names_the_owning_session(orm_db):
    chunking = ChunkingService(orm_db, {})

    assert chunking.build_chunk_set_signature(
        1, [5], CONFIG
    ) != chunking.build_chunk_set_signature(2, [5], CONFIG)
    assert chunking.build_chunk_set_signature(
        1, [5, 6], CONFIG
    ) == chunking.build_chunk_set_signature(1, [6, 5], CONFIG)


def test_two_sessions_never_share_a_chunk_set(orm_db, tmp_path):
    first = _insert_rag_session(orm_db, "own_a")
    second = _insert_rag_session(orm_db, "own_b")
    document = _insert_data_document(orm_db, tmp_path, "own.txt", ["text"])
    chunking = ChunkingService(orm_db, {})

    first_set = chunking.get_or_create_chunk_set(first.id, [document.id], CONFIG)
    again = chunking.get_or_create_chunk_set(first.id, [document.id], CONFIG)
    second_set = chunking.get_or_create_chunk_set(second.id, [document.id], CONFIG)

    assert again.id == first_set.id
    assert second_set.id != first_set.id
    assert (first_set.session_id, second_set.session_id) == (first.id, second.id)
