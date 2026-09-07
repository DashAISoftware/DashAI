"""Unit tests for the cross-encoder re-ranker and the RAG cleanup config match.

Covers :class:`CrossEncoderRetriever` behavior through a deterministic
fake cross-encoder subclass, and includes a regression test for the
SQLAlchemy ``filter`` bug fixed in
:mod:`DashAI.back.services.RAG.cleanup_service`.
"""

import numpy as np
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from DashAI.back.dependencies.database.models import Base, GenerativeSession
from DashAI.back.models.RAG.documents import Chunk
from DashAI.back.models.RAG.exceptions import (
    RAGRetrieverEmptyChildrenError,
    RAGRetrieverError,
)
from DashAI.back.models.RAG.retrievers.composite.mmr_reranker_retriever import (
    MMRRerankerRetriever,
)
from DashAI.back.models.RAG.retrievers.cross_encoder import (
    SentenceTransformerCrossEncoderRetriever,
)
from DashAI.back.models.RAG.retrievers.cross_encoder.cross_encoder_retriever import (
    CrossEncoderRetriever,
)
from DashAI.back.models.RAG.retrievers.retriever_model import RetrieverModel
from DashAI.back.services.RAG.cleanup_service import CleanupService


def _make_chunk(chunk_id: int, doc_id: int = 1) -> Chunk:
    """Build a Chunk with deterministic fields."""
    return Chunk(chunk_id, doc_id, chunk_id, f"chunk-{chunk_id}")


class _FakeChildRetriever(RetrieverModel):
    """In-memory child retriever with configurable chunks and vectors."""

    def __init__(self, chunks, vectors=None, default_top_k: int | None = None):
        """Initialize with the chunks it will return.

        Args:
            chunks: Chunks this child can retrieve.
            vectors: Optional vector matrix; defaults to zeros.
            default_top_k: Number of chunks returned when ``retrieve`` is
                called without a ``top_k`` override. When ``None``, all
                chunks are returned (mimicking a child whose own top-k is
                the full candidate set).
        """
        super().__init__()
        self._chunks = chunks
        if vectors is None:
            vectors = np.zeros((len(chunks), 2))
        self._vectors = vectors
        self._default_top_k = default_top_k
        self.retrieve_calls = []

    def retrieve(self, query: str, top_k: int | None = None, **kwargs):
        """Return the configured chunks, trimmed to the effective top_k."""
        self.retrieve_calls.append((query, top_k))
        if top_k is None:
            top_k = self._default_top_k
        if top_k is None:
            return list(self._chunks)
        return list(self._chunks[:top_k])

    def score_chunks(self, chunk_ids, query):
        """Return a constant distance for every requested chunk."""
        return [(cid, 0.5) for cid in chunk_ids]

    def get_chunk_vectors(self, chunk_ids):
        """Return the configured vectors for the requested chunks."""
        return self._vectors[: len(chunk_ids)]

    @property
    def retrieval_top_k(self) -> int:
        """Return the total number of configured chunks."""
        return len(self._chunks)


class _FakeCrossEncoderRetriever(CrossEncoderRetriever):
    """Concrete cross-encoder whose scores come from a fixed map."""

    def __init__(self, scores=None, **kwargs):
        """Initialize and store the fake score map."""
        super().__init__(**kwargs)
        self._scores = scores or {}

    def _cross_score(self, query: str, chunks) -> list[float]:
        """Return the configured fake score for each chunk in order."""
        return [self._scores.get(chunk.id, 0.0) for chunk in chunks]


class _FakeNLICrossEncoder:
    """Fake cross-encoder whose ``predict`` returns ``(n, 3)`` logits."""

    def __init__(self, logits):
        """Initialize with the 2D logit array to return."""
        self._logits = logits

    def predict(self, pairs, **kwargs):
        """Return the pre-configured 2D logit array."""
        return np.asarray(self._logits)


class _FakeVectorsUnavailableChild(RetrieverModel):
    """Child that scores chunks but raises on ``get_chunk_vectors``."""

    def __init__(self, chunks):
        """Initialize with the chunks it will return."""
        super().__init__()
        self._chunks = chunks

    def retrieve(self, query: str, top_k: int | None = None, **kwargs):
        """Return the configured chunks, trimmed to top_k when given."""
        if top_k is None:
            return list(self._chunks)
        return list(self._chunks[:top_k])

    def score_chunks(self, chunk_ids, query):
        """Return a constant distance for every requested chunk."""
        return [(cid, 0.5) for cid in chunk_ids]

    def get_chunk_vectors(self, chunk_ids):
        """Raise to signal that no vectors are available."""
        raise RAGRetrieverError("child retriever has no chunk vectors")

    @property
    def retrieval_top_k(self) -> int:
        """Return the total number of configured chunks."""
        return len(self._chunks)


def test_retrieve_uses_configured_top_k_and_honors_override():
    """Default retrieval returns ``_top_k`` items; an override wins over it.

    The child is invoked with no ``top_k`` override: its own configuration
    drives the candidate count.
    """
    chunks = [_make_chunk(i) for i in range(10)]
    child = _FakeChildRetriever(chunks)
    retriever = _FakeCrossEncoderRetriever(
        children=[child],
        top_k=3,
        scores={c.id: float(10 - c.id) for c in chunks},
    )

    default_result = retriever.retrieve("query")
    assert len(default_result) == 3
    assert child.retrieve_calls[-1] == ("query", None)

    override_result = retriever.retrieve("query", top_k=2)
    assert len(override_result) == 2
    assert child.retrieve_calls[-1] == ("query", None)


def test_retrieve_returns_candidates_in_child_order_below_top_k():
    """When candidates do not exceed the effective top-k, no re-scoring runs."""
    chunks = [_make_chunk(i) for i in range(3)]
    child = _FakeChildRetriever(chunks)
    retriever = _FakeCrossEncoderRetriever(
        children=[child],
        top_k=5,
    )

    result = retriever.retrieve("query")
    assert result == chunks
    assert child.retrieve_calls[-1] == ("query", None)


def test_retrieve_candidate_set_capped_by_child_own_top_k():
    """The child's own top_k caps the candidate set; the reranker cannot expand it.

    The child returns only its ``default_top_k`` candidates, which is below
    the reranker's ``top_k``, so the reranker short-circuits and can only
    return what the child retrieved. If the reranker inflated the candidate
    set (old ``retrieval_factor`` behavior) it would return ``top_k`` items
    instead.
    """
    chunks = [_make_chunk(i) for i in range(10)]
    child = _FakeChildRetriever(chunks, default_top_k=2)
    retriever = _FakeCrossEncoderRetriever(
        children=[child],
        top_k=5,
    )

    result = retriever.retrieve("query")

    assert child.retrieve_calls[-1] == ("query", None)
    assert len(result) == 2


def test_retrieve_rejects_top_k_below_one():
    """``retrieve`` raises RAGRetrieverError for top_k of 0 or negative."""
    child = _FakeChildRetriever([_make_chunk(i) for i in range(5)])
    retriever = _FakeCrossEncoderRetriever(
        children=[child],
        top_k=3,
    )

    for bad_k in (0, -1, -5):
        with pytest.raises(RAGRetrieverError, match="top_k"):
            retriever.retrieve("query", top_k=bad_k)


def test_score_chunks_returns_sorted_distances():
    """Distances are in [0, 1], ascending, with lower distance for higher logit."""
    chunks_map = {
        1: {
            11: Chunk(11, 1, 0, "alpha"),
            12: Chunk(12, 1, 1, "beta"),
            13: Chunk(13, 1, 2, "gamma"),
        }
    }
    child = _FakeChildRetriever([])
    retriever = _FakeCrossEncoderRetriever(
        children=[child],
        top_k=2,
        scores={11: 10.0, 12: 0.0, 13: -10.0},
    )
    retriever.inject_infra("path", chunks_map, None)

    result = retriever.score_chunks([13, 12, 11], "query")

    assert [cid for cid, _ in result] == [11, 12, 13]
    assert all(0.0 <= dist <= 1.0 for _, dist in result)
    assert result[0][0] == 11
    assert result[-1][0] == 13


def test_score_chunks_handles_subset_of_valid_ids():
    """Unknown chunk IDs are skipped and only valid IDs are scored."""
    chunks_map = {
        1: {
            11: Chunk(11, 1, 0, "alpha"),
            12: Chunk(12, 1, 1, "beta"),
        }
    }
    child = _FakeChildRetriever([])
    retriever = _FakeCrossEncoderRetriever(
        children=[child],
        top_k=2,
        scores={11: 5.0},
    )
    retriever.inject_infra("path", chunks_map, None)

    result = retriever.score_chunks([11, 999], "query")

    assert [cid for cid, _ in result] == [11]


def test_score_chunks_returns_empty_when_no_id_found():
    """An empty result is returned when no requested ID is in the corpus."""
    child = _FakeChildRetriever([])
    retriever = _FakeCrossEncoderRetriever(
        children=[child],
        top_k=2,
    )
    retriever.inject_infra("path", {1: {}}, None)

    assert retriever.score_chunks([999], "query") == []


def test_score_chunks_raises_without_injected_infra():
    """scoring before ``inject_infra`` raises RAGRetrieverError."""
    child = _FakeChildRetriever([])
    retriever = _FakeCrossEncoderRetriever(
        children=[child],
        top_k=2,
    )

    with pytest.raises(RAGRetrieverError, match="inject_infra"):
        retriever.score_chunks([1], "query")


def test_get_chunk_vectors_delegates_to_child():
    """``get_chunk_vectors`` forwards to the child and returns its result."""
    chunks = [_make_chunk(i) for i in range(3)]
    child = _FakeChildRetriever(chunks)
    retriever = _FakeCrossEncoderRetriever(
        children=[child],
        top_k=1,
    )

    vectors = retriever.get_chunk_vectors([0, 1, 2])

    assert vectors.shape == (3, 2)
    assert np.array_equal(vectors, np.zeros((3, 2)))


def test_get_chunk_vectors_raises_when_child_unsupported():
    """A child without ``get_chunk_vectors`` raises RAGRetrieverError."""
    chunks = [_make_chunk(i) for i in range(3)]
    child = _FakeChildRetriever(chunks)
    child.get_chunk_vectors = None
    retriever = _FakeCrossEncoderRetriever(
        children=[child],
        top_k=1,
    )

    with pytest.raises(RAGRetrieverError, match="does not support"):
        retriever.get_chunk_vectors([0])


def test_save_raises_not_implemented():
    """The abstract base has no persisted state, so save() is unsupported."""
    child = _FakeChildRetriever([])
    retriever = _FakeCrossEncoderRetriever(
        children=[child],
        top_k=1,
    )

    with pytest.raises(NotImplementedError, match="no persisted state"):
        retriever.save()


def test_init_model_delegates_to_load():
    """``init_model`` calls the subclass ``load`` override once."""
    child = _FakeChildRetriever([])

    class _LoadSpyRetriever(_FakeCrossEncoderRetriever):
        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            self.load_calls = 0

        def load(self, filename: str = "") -> None:
            self.load_calls += 1

    spy = _LoadSpyRetriever(children=[child], top_k=1)

    spy.init_model()

    assert spy.load_calls == 1


def test_cross_score_collapses_multilabel_logits():
    """``_cross_score`` selects the score_index column for NLI-style models."""
    child = _FakeChildRetriever([_make_chunk(i) for i in range(2)])
    retriever = SentenceTransformerCrossEncoderRetriever(
        model_name="cross-encoder/nli-distilroberta-base",
        children=[child],
        top_k=1,
    )
    retriever._ce_model = _FakeNLICrossEncoder([[0.1, 2.5, -1.0], [0.2, -0.5, 1.0]])
    chunks = [_make_chunk(1), _make_chunk(2)]

    scores = retriever._cross_score("query", chunks)

    assert scores == [2.5, -0.5]


def test_cross_score_rejects_multilabel_without_score_index():
    """``_cross_score`` raises when a 2D result has no configured score_index."""
    retriever = SentenceTransformerCrossEncoderRetriever(
        model_name="cross-encoder/ms-marco-MiniLM-L-6-v2",
        children=[_FakeChildRetriever([])],
        top_k=1,
    )
    retriever._ce_model = _FakeNLICrossEncoder([[0.1, 2.5, -1.0]])

    with pytest.raises(RAGRetrieverError, match="score_index"):
        retriever._cross_score("query", [_make_chunk(1)])


def test_load_rejects_unknown_model_name():
    """``load`` raises RAGRetrieverError before any HF download."""
    retriever = SentenceTransformerCrossEncoderRetriever(
        model_name="not-a-model",
        children=[_FakeChildRetriever([])],
        top_k=1,
    )

    with pytest.raises(RAGRetrieverError, match="Unknown cross-encoder model"):
        retriever.load()

    assert retriever._ce_model is None


def test_retrieve_rejects_non_integer_top_k():
    """``retrieve`` raises RAGRetrieverError for non-int or invalid top_k."""
    retriever = _FakeCrossEncoderRetriever(
        children=[_FakeChildRetriever([_make_chunk(i) for i in range(5)])],
        top_k=3,
    )

    for bad_k in ("5", 0, -1):
        with pytest.raises(RAGRetrieverError, match="top_k"):
            retriever.retrieve("query", top_k=bad_k)


def test_retrieve_raises_when_no_children():
    """``retrieve`` raises RAGRetrieverEmptyChildrenError without children."""
    retriever = _FakeCrossEncoderRetriever(
        children=[],
        top_k=3,
    )

    with pytest.raises(RAGRetrieverEmptyChildrenError, match="child retriever"):
        retriever.retrieve("query")


def test_get_chunk_vectors_raises_when_no_children():
    """``get_chunk_vectors`` raises RAGRetrieverEmptyChildrenError without children."""
    retriever = _FakeCrossEncoderRetriever(
        children=[],
        top_k=3,
    )

    with pytest.raises(RAGRetrieverEmptyChildrenError, match="child retriever"):
        retriever.get_chunk_vectors([1])


def test_mmr_falls_back_when_child_vectors_unavailable():
    """MMR falls back to ordered top-k when the child cannot supply vectors."""
    chunks = [_make_chunk(i) for i in range(6)]
    child = _FakeVectorsUnavailableChild(chunks)
    mmr = MMRRerankerRetriever(
        children=[child],
        mmr_lambda=0.5,
        top_k=3,
    )

    result = mmr.retrieve("query")

    assert [c.id for c in result] == [0, 1, 2]


def test_other_sessions_with_same_config_ignores_list_order():
    """Config matching treats document lists as equal regardless of order."""
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()
    try:
        parameters = {
            "documents": [1, 2],
            "chunking_model": {
                "component": "CharacterChunkModel",
                "params": {"chunk_size": 400},
            },
        }
        db.add(
            GenerativeSession(
                id=1,
                task_name="RAGTask",
                model_name="RAGPipeline",
                parameters=parameters,
                name="session-one",
            )
        )
        db.add(
            GenerativeSession(
                id=2,
                task_name="RAGTask",
                model_name="RAGPipeline",
                parameters={"documents": [2, 1]},
                name="session-two",
            )
        )
        db.commit()

        service = CleanupService(db)
        assert (
            service._other_sessions_with_same_config(1, parameters, keys=("documents",))
            is True
        )
    finally:
        db.close()
        engine.dispose()


def test_other_sessions_with_same_config_ignores_current_session():
    """Cleanup config matching excludes the current session and finds others."""
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()
    try:
        parameters = {
            "documents": [1],
            "chunking_model": {
                "component": "CharacterChunkModel",
                "params": {"chunk_size": 400},
            },
        }
        db.add(
            GenerativeSession(
                id=1,
                task_name="RAGTask",
                model_name="RAGPipeline",
                parameters=parameters,
                name="session-one",
            )
        )
        db.commit()

        service = CleanupService(db)
        assert (
            service._other_sessions_with_same_config(1, parameters, keys=("documents",))
            is False
        )

        db.add(
            GenerativeSession(
                id=2,
                task_name="RAGTask",
                model_name="RAGPipeline",
                parameters=parameters,
                name="session-two",
            )
        )
        db.commit()
        assert (
            service._other_sessions_with_same_config(1, parameters, keys=("documents",))
            is True
        )
    finally:
        db.close()
        engine.dispose()
