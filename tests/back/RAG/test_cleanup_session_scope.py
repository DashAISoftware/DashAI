"""Index cleanup never leaves the session it was asked to clean."""

import uuid

from DashAI.back.dependencies.database.models import Chunk as ChunkRow
from DashAI.back.dependencies.database.models import (
    RAGChunkSet,
    RAGChunkSetDocument,
    RAGPipeline,
    RAGRetriever,
    RAGSparseRetriever,
)
from DashAI.back.services.RAG.cleanup_service import CleanupService
from tests.back.RAG.conftest import _insert_data_document, _insert_rag_session


def _chunk_set_with_sparse_index(db, session_id, document_id, storage) -> int:
    """Insert a chunk set with one chunk and a fitted sparse retriever.

    Parameters
    ----------
    db : Session
        Database session to write with.
    session_id : int or None
        Owning session, None for a legacy chunk set.
    document_id : int
        Document the chunk belongs to.
    storage : pathlib.Path
        Folder created as the retriever storage.

    Returns
    -------
    int
        The chunk set id.
    """
    chunk_set = RAGChunkSet(
        signature=uuid.uuid4().hex, parameters={}, session_id=session_id
    )
    db.add(chunk_set)
    db.flush()
    db.add(RAGChunkSetDocument(chunk_set_id=chunk_set.id, document_id=document_id))
    db.add(
        ChunkRow(
            chunk_set_id=chunk_set.id, document_id=document_id, chunk_index=0, text="t"
        )
    )
    pipeline = RAGPipeline(
        session_id=session_id if session_id is not None else 0, name=""
    )
    db.add(pipeline)
    db.flush()
    bridge = RAGRetriever(class_name="BM25Retriever", pipeline_id=pipeline.id)
    db.add(bridge)
    db.flush()
    storage.mkdir(parents=True)
    db.add(
        RAGSparseRetriever(
            bridge_id=bridge.id,
            chunk_set_id=chunk_set.id,
            class_name="BM25Retriever",
            parameters={},
            storage_folder=str(storage),
        )
    )
    db.commit()
    return chunk_set.id


def test_invalidating_a_session_leaves_other_sessions_alone(orm_db, tmp_path):
    first = _insert_rag_session(orm_db, "scope_a")
    second = _insert_rag_session(orm_db, "scope_b")
    document = _insert_data_document(orm_db, tmp_path / "docs", "shared.txt", ["s"])
    first_set = _chunk_set_with_sparse_index(
        orm_db, first.id, document.id, tmp_path / "a"
    )
    second_set = _chunk_set_with_sparse_index(
        orm_db, second.id, document.id, tmp_path / "b"
    )

    CleanupService(orm_db).invalidate_session_artifacts(first.id)

    assert orm_db.get(RAGChunkSet, first_set) is None
    assert orm_db.query(ChunkRow).filter_by(chunk_set_id=first_set).count() == 0
    assert orm_db.get(RAGChunkSet, second_set) is not None
    assert orm_db.query(ChunkRow).filter_by(chunk_set_id=second_set).count() == 1
    assert not (tmp_path / "a").exists()
    assert (tmp_path / "b").exists()


def test_legacy_chunk_sets_are_the_ones_without_a_session(orm_db, tmp_path):
    owner = _insert_rag_session(orm_db, "scope_owner")
    document = _insert_data_document(orm_db, tmp_path / "docs", "c.txt", ["c"])
    legacy_set = _chunk_set_with_sparse_index(
        orm_db, None, document.id, tmp_path / "legacy"
    )
    owned_set = _chunk_set_with_sparse_index(
        orm_db, owner.id, document.id, tmp_path / "owned"
    )

    assert CleanupService(orm_db).invalidate_legacy_artifacts() == 1

    assert orm_db.get(RAGChunkSet, legacy_set) is None
    assert orm_db.get(RAGChunkSet, owned_set) is not None
    assert not (tmp_path / "legacy").exists()
    assert (tmp_path / "owned").exists()
