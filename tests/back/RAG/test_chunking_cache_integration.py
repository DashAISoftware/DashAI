"""Integration test reproducing the production symptom of the RAG chunking cache bug.

This is a regression test for the fix: the final assertion previously
FAILED against the buggy implementation and now PASSES.

Production symptom
------------------
``ChunkingService.create`` (``DashAI/back/services/RAG/chunking_service.py``)
uses only ``(class_name, parameters)`` as the natural key of the chunking
model.  The chunk set (which encodes the document set) is NOT part of the key.

When the SAME chunking configuration is applied to a SECOND, different
document set:

1. The first document set creates the ``RAGChunkingModel`` record and
   persists its chunks under ``chunk_set_id=A``.
2. The second document set finds the cached model and takes the cache path:
   ``_fetch_chunks_from_db(chunk_set_id=B)`` returns ``{}`` because chunk
   set B has no persisted chunks yet.
3. ``ChunkingService.create`` returns a ``ChunkingFactoryResult`` whose
   ``chunks`` dict is EMPTY for chunk set B.
4. The dense retriever receives 0 chunks -> its ``DensePersistence`` has no
   ``matrix_dirs`` -> ``init_similarity_matrix()`` never builds a matrix ->
   ``res_b.model.similarity_matrix is None``.

At query time ``DenseRetriever.retrieve()`` raises
``ValueError: Similarity matrix not initialized.``
(``DashAI/back/models/RAG/retrievers/dense/dense_retriever.py``).

Invariant
---------
Every newly created chunk set must have its chunks computed and persisted,
even when the chunking model is already cached for other documents.
"""

import contextlib
import os
import tempfile
import uuid

from fastapi.testclient import TestClient

from DashAI.back.dependencies.database.models import GenerativeSession, RAGPipeline
from DashAI.back.services.RAG.chunking_service import ChunkingService
from DashAI.back.services.RAG.document_service import DocumentService
from DashAI.back.services.RAG.retriever_setup_service import RetrieverSetupService
from tests.back.RAG.conftest import _create_test_document

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Chunking configuration shared by BOTH document sets (intentionally identical).
CHUNKING_CONFIG = {
    "chunking_model": {
        "component": "CharacterChunkModel",
        "params": {"chunk_size": 200, "chunk_overlap": 20},
    }
}

CHUNK_PARAMS = {"chunk_size": 200, "chunk_overlap": 20}

# Dense retriever configuration (real embedding model, no LLM involved).
DENSE_PARAMS = {
    "embedding_model": {
        "component": "SentenceTransformerEmbedding",
        "params": {
            "model_name": "sentence-transformers/all-MiniLM-L6-v2",
            "normalize": True,
            "device": "cpu",
            "overflow_strategy": "truncate",
        },
    },
    "similarity_metric": "cosine",
    "top_k": 5,
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

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _write_real_doc(client: TestClient, suffix: str, text: str) -> tuple[int, str]:
    """Create a document DB row AND its physical ``.txt`` file.

    ``_create_test_document`` only inserts the DB row; the physical file
    must exist so ``TxtDocument.get_text()`` can read it during chunking.
    The suffix (uuid-based) makes the ``file_hash`` unique per run.

    Returns:
        ``(doc_id, file_path)``.
    """
    doc_id = _create_test_document(client, suffix=suffix)
    file_path = os.path.join(tempfile.gettempdir(), f"test_doc{suffix}.txt")
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(text)
    return doc_id, file_path


def _create_session_and_pipeline(
    db, session_name: str
) -> tuple[GenerativeSession, RAGPipeline]:
    """Create a real ``GenerativeSession`` + ``RAGPipeline`` DB record pair.

    Returns:
        The freshly created (and committed/refreshed) session and pipeline.
    """
    session = GenerativeSession(
        task_name="RAGTask",
        model_name="RAGPipeline",
        parameters={},
        name=session_name,
        description=None,
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    pipeline = RAGPipeline(
        session_id=session.id,
        name="",
        description=None,
        parameters=None,
    )
    db.add(pipeline)
    db.commit()
    db.refresh(pipeline)
    return session, pipeline


# ---------------------------------------------------------------------------
# Integration test (regression)
# ---------------------------------------------------------------------------


def test_second_document_set_builds_similarity_matrix(client: TestClient):
    """Two distinct document sets sharing a chunking config must BOTH build
    a dense retriever similarity matrix.

    Scenario
    --------
    1. Two real ``.txt`` documents (A and B) are loaded.
    2. The same chunking config is applied to each document set, creating
       two distinct chunk sets.
    3. A dense retriever (``DenseEmbeddingRetriever``) is set up for each
       chunk set through ``RetrieverSetupService``.

    Expected
    --------
    - ``res_a.model.similarity_matrix`` is not ``None`` (sanity check:
      the first document set constructs the matrix).
    - ``res_b.model.similarity_matrix`` is not ``None`` (the production
      invariant: every chunk set must have its chunks computed).

    Regression
    ----------
    Before the fix, ``result_b.chunks`` was ``{}`` because
    ``ChunkingService.create`` hit the cached chunking model and returned
    no chunks for chunk set B.  The dense retriever therefore initialized
    ``similarity_matrix`` to ``None`` and the final assertion FAILED —
    reproducing the production error "Similarity matrix not initialized".
    """
    run_tag = uuid.uuid4().hex[:8]

    # ---- create real documents on disk (docs A and B) ----
    doc_a_id, path_a = _write_real_doc(client, f"_{run_tag}_int_a", DOC_A_TEXT)
    doc_b_id, path_b = _write_real_doc(client, f"_{run_tag}_int_b", DOC_B_TEXT)
    written_paths = [path_a, path_b]

    registry = client.app.container["component_registry"]
    session_factory = client.app.container["session_factory"]
    rag_path = str(client.app.container["config"]["RAG_PATH"])

    try:
        with session_factory() as db:
            doc_service = DocumentService(db)
            docs_a = doc_service.load([doc_a_id])
            docs_b = doc_service.load([doc_b_id])

            chunking = ChunkingService(db, registry)

            # ---- pipeline DB records (one per document set) ----
            _session_a, pipeline_a = _create_session_and_pipeline(
                db, f"cache_int_session_a_{run_tag}"
            )
            _session_b, pipeline_b = _create_session_and_pipeline(
                db, f"cache_int_session_b_{run_tag}"
            )

            # ---- document set A: creates the chunking model + chunks ----
            chunk_set_a = chunking.get_or_create_chunk_set([doc_a_id], CHUNKING_CONFIG)
            _record_a, result_a = chunking.create(
                docs_a,
                chunk_set_a.id,
                "CharacterChunkModel",
                CHUNK_PARAMS,
            )
            assert result_a.chunks, (
                "Sanity check failed: the first document set should produce "
                f"chunks, got {result_a.chunks!r}"
            )

            # ---- document set B: same config, different documents ----
            chunk_set_b = chunking.get_or_create_chunk_set([doc_b_id], CHUNKING_CONFIG)
            assert chunk_set_b.id != chunk_set_a.id, (
                "Chunk sets must be distinct (different document IDs)."
            )
            _record_b, result_b = chunking.create(
                docs_b,
                chunk_set_b.id,
                "CharacterChunkModel",
                CHUNK_PARAMS,
            )

            # ---- dense retriever for chunk set A (sanity) ----
            svc_a = RetrieverSetupService(
                db,
                registry,
                rag_path,
                result_a.chunks,
                chunk_set_a.id,
                pipeline_a.id,
            )
            res_a = svc_a.setup("DenseEmbeddingRetriever", DENSE_PARAMS)
            assert res_a.model.similarity_matrix is not None, (
                "Sanity check failed: the first chunk set should have built "
                "a similarity matrix."
            )

            # ---- dense retriever for chunk set B (production symptom) ----
            svc_b = RetrieverSetupService(
                db,
                registry,
                rag_path,
                result_b.chunks,
                chunk_set_b.id,
                pipeline_b.id,
            )
            res_b = svc_b.setup("DenseEmbeddingRetriever", DENSE_PARAMS)

            # INVARIANT: a newly created chunk set must produce a similarity
            # matrix.  With the current code result_b.chunks is empty, the
            # retriever's matrix_dirs are empty, and similarity_matrix stays
            # None (the exact production symptom).
            assert res_b.model.similarity_matrix is not None, (
                "BUG: the second chunk set did not build a similarity matrix. "
                "ChunkingService.create returned empty chunks for chunk_set_b "
                f"(id={chunk_set_b.id}) because the chunking model was already "
                f"cached for chunk_set_a (id={chunk_set_a.id}) with the same "
                f"(class_name, parameters) key. Every newly created chunk set "
                "must have its chunks computed and persisted even when the "
                "chunking model is already cached. Production symptom: "
                "'ValueError: Similarity matrix not initialized'."
            )
    finally:
        with contextlib.suppress(OSError):
            for file_path in written_paths:
                os.remove(file_path)
