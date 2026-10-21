"""Unit tests for the iterative retrieval pool."""

from __future__ import annotations

from typing import Dict, List

import pytest

from DashAI.back.models.RAG.documents import Chunk
from DashAI.back.models.RAG.exceptions.retriever import RAGRetrieverEvaluationError
from DashAI.back.models.RAG.retrievers.composite.retrieval_context import (
    RetrievalContext,
)
from DashAI.back.models.RAG.retrievers.composite.retrieval_pool import RetrievalPool


def _chunks(count: int, document_id: int = 1) -> List[Chunk]:
    """Build ``count`` persisted-looking chunks for one document."""
    return [
        Chunk(
            id=document_id * 100 + position,
            document_id=document_id,
            document_position=position,
            text=f"chunk-{document_id}-{position}",
        )
        for position in range(count)
    ]


def _context(chunks: List[Chunk]) -> RetrievalContext:
    """Build a retrieval context over the injected corpus."""
    grouped: Dict[int, Dict[int, Chunk]] = {}
    for chunk in chunks:
        grouped.setdefault(chunk.document_id, {})[chunk.id] = chunk
    return RetrievalContext({}, grouped)


def _positions(pool: RetrievalPool) -> List[int]:
    """Return the document positions of the materialized pool."""
    return [chunk.document_position for chunk in pool.materialize()]


def test_add_deduplicates_and_preserves_first_seen_order():
    """Repeated chunks are ignored and insertion order is preserved."""
    chunks = _chunks(4)
    pool = RetrievalPool(10, _context(chunks))

    pool.add([chunks[2], chunks[0], chunks[2], chunks[1]])

    assert _positions(pool) == [2, 0, 1]
    assert pool.size() == 3


def test_request_includes_a_chunk_no_retriever_returned():
    """Requested chunks are resolved from the corpus and come first."""
    chunks = _chunks(5)
    pool = RetrievalPool(10, _context(chunks))
    pool.add(chunks[:2])

    pool.request({1: [4]})

    assert _positions(pool) == [4, 0, 1]


def test_request_unknown_position_raises_actionable_error():
    """A requested position absent from the corpus fails loudly."""
    pool = RetrievalPool(10, _context(_chunks(2)))

    with pytest.raises(RAGRetrieverEvaluationError, match="document 1"):
        pool.request({1: [9]})


def test_discard_filters_later_returns():
    """A discarded chunk stays excluded when a later round returns it."""
    chunks = _chunks(5)
    pool = RetrievalPool(10, _context(chunks))
    pool.add(chunks[:3])
    pool.discard({1: [1]})

    pool.add(chunks[1:4])

    assert _positions(pool) == [0, 2, 3]


@pytest.mark.parametrize(
    "mapping",
    [{1: [999]}, {424242: [0]}],
)
def test_discard_unknown_chunk_raises(mapping):
    """Discarding a non-existent position or document fails loudly."""
    pool = RetrievalPool(10, _context(_chunks(3)))

    with pytest.raises(RAGRetrieverEvaluationError, match="does not exist"):
        pool.discard(mapping)


def test_newest_request_batch_is_not_starved_by_the_cap():
    """The newest request is materialized even when older ones fill the cap."""
    chunks = _chunks(6)
    pool = RetrievalPool(2, _context(chunks))

    pool.request({1: [4, 5]})
    pool.request({1: [3]})

    assert _positions(pool) == [3, 4]


def test_re_requesting_moves_key_into_the_newest_batch():
    """Re-requesting an existing key keeps membership and refreshes priority."""
    chunks = _chunks(6)
    pool = RetrievalPool(2, _context(chunks))
    pool.request({1: [4, 5]})

    pool.request({1: [5]})

    assert _positions(pool) == [5, 4]


def test_requested_then_discarded_is_excluded():
    """A discard after a request removes the chunk (last action wins)."""
    chunks = _chunks(3)
    pool = RetrievalPool(10, _context(chunks))
    pool.add(chunks)

    pool.request({1: [1]})
    pool.discard({1: [1]})

    assert _positions(pool) == [0, 2]


def test_discarded_then_requested_is_included():
    """A request after a discard re-includes the chunk (last action wins)."""
    chunks = _chunks(3)
    pool = RetrievalPool(10, _context(chunks))
    pool.add(chunks)

    pool.discard({1: [1]})
    assert _positions(pool) == [0, 2]

    pool.request({1: [1]})
    assert _positions(pool) == [1, 0, 2]


def test_request_discard_request_sequence_last_action_wins():
    """A request after a discard re-includes the chunk in the same pool."""
    chunks = _chunks(3)
    pool = RetrievalPool(10, _context(chunks))
    pool.add(chunks)

    pool.request({1: [1]})
    pool.discard({1: [1]})
    pool.request({1: [1]})

    assert _positions(pool) == [1, 0, 2]


def test_corpus_accessor_is_deeply_read_only():
    """Nested chunk mappings cannot be mutated through the accessor."""
    context = _context(_chunks(2))

    with pytest.raises(TypeError):
        context.corpus()[1][100] = _chunks(1)[0]


def test_document_payload_keeps_missing_name_as_none():
    """The context does not build display names for missing documents."""
    context = _context(_chunks(2))

    payload = context.document_payload()

    assert payload == [{"document_id": 1, "name": None, "chunks": 2, "pages": 0}]


def test_materialize_truncates_to_max_chunks_after_prioritizing_requests():
    """Requested chunks survive the cap before the remaining ones."""
    chunks = _chunks(6)
    pool = RetrievalPool(3, _context(chunks))
    pool.add(chunks)

    pool.request({1: [5]})

    assert _positions(pool) == [5, 0, 1]
    assert pool.size() == 3
