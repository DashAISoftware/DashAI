"""Regression tests for the dense retriever chunk-id space.

Chunk objects carry two identifiers that differ in production:
``Chunk.id`` is the persistent DB primary key (global autoincrement),
while the ``chunks`` dict is keyed by the chunk *index* (0-based position
within a document).  Composite retrievers (MMR reranker, sequential,
parallel, cross-encoder) call ``score_chunks`` / ``get_chunk_vectors``
with ``Chunk.id`` values, so the dense retriever must index its
similarity matrix by ``Chunk.id`` — not by the dict key.

These tests build chunks whose DB ids are offset from their indices to
mirror a persistent database where the two never coincide.
"""

import os

import numpy as np

from DashAI.back.models.RAG.documents import Chunk
from DashAI.back.models.RAG.retrievers.composite.mmr_reranker_retriever import (
    MMRRerankerRetriever,
)
from DashAI.back.models.RAG.retrievers.dense.dense_embedding_retriever import (
    DenseEmbeddingRetriever,
)
from DashAI.back.models.RAG.retrievers.persistence import DensePersistence


class _FakeEmbedding:
    """In-memory DenseEmbedding stand-in with deterministic vectors."""

    def __init__(self):
        self.rng = np.random.RandomState(42)
        self.dim = 8
        self.params = {"model_name": "fake", "device": "cpu"}

    def load(self):
        return None

    def encode(self, text):
        vector = self.rng.rand(self.dim)
        return vector / np.linalg.norm(vector)

    def batch_encode(self, texts):
        return np.array([self.encode(t) for t in texts])


def _build_chunks(n_chunks: int, doc_id: int = 1, id_offset: int = 500):
    """Return ``{doc_id: {index: Chunk}}`` with DB ids != indices."""
    chunks = {}
    for idx in range(n_chunks):
        chunks[idx] = Chunk(
            id=id_offset + idx,
            document_id=doc_id,
            document_position=idx,
            text=f"chunk {idx} about retrieval augmented generation",
        )
    return {doc_id: chunks}


def _build_dense_retriever(n_chunks: int):
    """Build a DenseEmbeddingRetriever with a persisted embedding matrix."""
    chunks = _build_chunks(n_chunks)
    embedding = _FakeEmbedding()
    matrix_dir = os.path.join(os.getcwd(), "_tmp_dense_matrix")
    os.makedirs(matrix_dir, exist_ok=True)
    try:
        texts = [chunk.text for chunk in chunks[1].values()]
        np.save(
            os.path.join(matrix_dir, "embeddings.npy"),
            embedding.batch_encode(texts),
        )
        persistence = DensePersistence(
            matrix_dirs={1: matrix_dir}, embedding_model_id=1
        )
        retriever = DenseEmbeddingRetriever(
            embedding_model=embedding,
            similarity_metric="cosine",
            top_k=10,
        )
        retriever.inject_infra(os.path.dirname(matrix_dir), chunks, persistence)
        retriever.embedding_model = embedding
        retriever.init_similarity_matrix()
        return retriever, chunks
    finally:
        os.remove(os.path.join(matrix_dir, "embeddings.npy"))
        os.rmdir(matrix_dir)


def test_dense_retriever_scores_chunks_by_db_id():
    """``score_chunks`` resolves chunk DB ids even when they differ from indices.

    Regression: the similarity matrix was previously keyed by the chunk
    index (dict key) while ``score_chunks`` received ``Chunk.id``, so any
    production DB whose autoincrement ids diverged from chunk positions
    returned an empty score list.
    """
    retriever, _ = _build_dense_retriever(n_chunks=30)

    candidates = retriever.retrieve("what is machine learning?")
    assert candidates, "retrieve returned no chunks"

    ids = [c.id for c in candidates]
    scored = retriever.score_chunks(ids, "what is machine learning?")
    assert len(scored) == len(ids)
    assert all(cid in ids for cid, _ in scored)


def test_mmr_reranker_returns_chunks_with_dense_child():
    """MMR over a dense child returns chunks in production id space.

    Regression: MMR calls ``child.score_chunks([c.id ...])`` and
    ``child.get_chunk_vectors([c.id ...])``; the dense child returned
    empty scores, so MMR retrieval produced no chunks.
    """
    child, chunks = _build_dense_retriever(n_chunks=30)
    mmr = MMRRerankerRetriever(children=[child], mmr_lambda=0.5, top_k=5)
    mmr.inject_infra(os.getcwd(), chunks, None)

    result = mmr.retrieve("what is machine learning?")

    assert len(result) == 5
    assert all(c.id is not None for c in result)
