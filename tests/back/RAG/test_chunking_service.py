"""Regression tests for RAG chunking chunk-set isolation.

Reproduces a known bug in ``ChunkingService.create``: the chunking model
lookup uses only ``(class_name, parameters)`` as its natural key, ignoring
the target ``chunk_set_id``.

When the SAME chunking configuration is applied to a SECOND, different
document set:

1. The first document set creates the ``RAGChunkingModel`` record and
   persists its chunks under the first ``chunk_set_id``.
2. The second document set finds the cached model, skips the pure factory,
   and calls ``_fetch_chunks_from_db(chunk_set_id)`` for a chunk set that
   has no persisted chunks yet -> returns ``{}``.
3. ``ChunkingService.create`` returns a ``ChunkingFactoryResult`` whose
   ``chunks`` dict is EMPTY for the new document set.

This violates the invariant that every newly created chunk set must have
its chunks computed and persisted, even when the chunking model is already
cached for other documents.  The symptom in production is the retriever
error "Similarity matrix not initialized" (the dense retriever receives
0 chunks).

This is a regression test for the fix: the final assertion previously
FAILED against the buggy implementation and now PASSES.
"""

import contextlib
import os
import tempfile
import uuid

import pytest
from fastapi.testclient import TestClient

from DashAI.back.services.RAG.chunking_service import ChunkingService
from DashAI.back.services.RAG.document_service import DocumentService
from tests.back.RAG.conftest import _create_test_document

# Chunking config shared by both document sets (intentionally identical).
CHUNKING_CONFIG = {
    "chunking_model": {
        "component": "CharacterChunkModel",
        "params": {"chunk_size": 200, "chunk_overlap": 20},
    }
}

# Real paragraphs (>200 chars each) so CharacterChunkModel produces chunks.
DOC_A_TEXT = (
    "DashAI is a graphical toolbox for training, evaluating and deploying "
    "machine learning models. It provides a complete graphical interface "
    "that allows users to compare and use different machine learning "
    "algorithms without writing code. The toolbox supports a wide range of "
    "classic and modern techniques and automates the tedious parts of the "
    "experimentation workflow, from dataset loading to deployment. "
) * 5

DOC_B_TEXT = (
    "Retrieval augmented generation combines a dense retriever with a large "
    "language model to answer questions grounded in a private document "
    "collection. Documents are loaded, split into chunks, embedded, and "
    "stored in a vector index. At query time the retriever fetches the most "
    "relevant chunks and the generator produces an answer using them as "
    "context, reducing hallucinations. "
) * 5


@pytest.fixture(scope="module")
def chunking_doc_ids(client: TestClient):
    """Create two real ``.txt`` documents on disk and their DB rows.

    ``_create_test_document`` only inserts the DB row; the physical file
    must be written so ``TxtDocument.get_text()`` can read it during
    chunking.  The file names/hashes include a random run tag so repeated
    runs never collide with stale ``document`` rows.
    """
    run_tag = uuid.uuid4().hex[:8]
    specs = [
        (f"_{run_tag}_chunk_reg_a", DOC_A_TEXT),
        (f"_{run_tag}_chunk_reg_b", DOC_B_TEXT),
    ]
    doc_ids = []
    written_paths = []
    try:
        for suffix, text in specs:
            doc_id = _create_test_document(client, suffix=suffix)
            file_path = os.path.join(tempfile.gettempdir(), f"test_doc{suffix}.txt")
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(text)
            written_paths.append(file_path)
            doc_ids.append(doc_id)
        yield doc_ids
    finally:
        with contextlib.suppress(OSError):
            for file_path in written_paths:
                os.remove(file_path)


def test_chunking_reuses_cached_model_with_empty_chunks_for_new_chunk_set(
    client: TestClient,
    chunking_doc_ids: list[int],
):
    """Two document sets sharing a chunking config must both get chunks.

    The first ``create`` call persists the chunking model record and the
    chunks for the first chunk set.  The second ``create`` call uses the
    same ``(class_name, parameters)`` key, hits the cache path, and returns
    empty chunks for the new chunk set.

    Regression: before the fix, ``assert result_b.chunks`` FAILED because
    the buggy code returned an empty dict for the new chunk set; now it
    PASSES.
    """
    doc_a_id, doc_b_id = chunking_doc_ids

    registry = client.app.container["component_registry"]
    session_factory = client.app.container["session_factory"]

    with session_factory() as db:
        doc_service = DocumentService(db)
        docs_a = doc_service.load([doc_a_id])
        docs_b = doc_service.load([doc_b_id])

        chunking = ChunkingService(db, registry)

        # ---- First document set: creates the chunking model record ----
        chunk_set_a = chunking.get_or_create_chunk_set([doc_a_id], CHUNKING_CONFIG)
        _record_a, result_a = chunking.create(
            docs_a,
            chunk_set_a.id,
            "CharacterChunkModel",
            {"chunk_size": 200, "chunk_overlap": 20},
        )
        assert result_a.chunks, (
            "Sanity check failed: the first document set should produce "
            f"chunks, got {result_a.chunks!r}"
        )

        # ---- Second document set: same config, different documents ----
        chunk_set_b = chunking.get_or_create_chunk_set([doc_b_id], CHUNKING_CONFIG)
        assert chunk_set_b.id != chunk_set_a.id, (
            "Chunk sets must be distinct (different document IDs)."
        )

        _record_b, result_b = chunking.create(
            docs_b,
            chunk_set_b.id,
            "CharacterChunkModel",
            {"chunk_size": 200, "chunk_overlap": 20},
        )

        # INVARIANT: a newly created chunk set must have its chunks computed
        # and persisted, even if the chunking model is already cached.
        assert result_b.chunks, (
            "BUG: the second chunk set returned empty chunks. Every newly "
            "created chunk set must have its chunks computed even when the "
            "chunking model is cached for other documents "
            f"(chunk_set_b.id={chunk_set_b.id}). Got {result_b.chunks!r}"
        )
