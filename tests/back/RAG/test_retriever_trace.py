"""Unit tests for the retriever trace contract.

Every ``retrieve()`` returns ``(chunks, trace)``. These tests pin the trace
node shape, the single-source chunk reference format, and the nesting of
composite children.
"""

from __future__ import annotations

from typing import Dict, List, Tuple
from unittest.mock import MagicMock

import pytest

from DashAI.back.models.RAG.documents import Chunk
from DashAI.back.models.RAG.retrievers.base_retriever import BaseRetriever
from DashAI.back.models.RAG.retrievers.composite.parallel_retriever import (
    ParallelRetriever,
)
from DashAI.back.models.RAG.retrievers.composite.sequential_retriever import (
    SequentialRetriever,
)
from DashAI.back.models.RAG.retrievers.trace_utils import chunk_ref, retriever_trace


def _chunk(doc_id: int, position: int) -> Chunk:
    """Build a persisted-looking chunk with a stable DB id."""
    return Chunk(
        id=doc_id * 100 + position,
        document_id=doc_id,
        document_position=position,
        text=f"d{doc_id}p{position}",
    )


class _StubRetriever(BaseRetriever):
    """Deterministic unit retriever returning a fixed chunk list."""

    def __init__(self, chunks: List[Chunk], top_k: int):
        """Store the chunks and configured top-k."""
        super().__init__()
        self._chunks = chunks
        self._top_k = top_k

    def retrieve(self, query: str, **kwargs) -> Tuple[List[Chunk], Dict[str, object]]:
        """Return the fixed chunks and their trace node."""
        chunks = list(self._chunks)
        return chunks, retriever_trace(self, chunks)

    def score_chunks(self, chunk_ids: List[int], query: str):
        """Return a constant distance for every requested chunk, in order."""
        return [(cid, 0.0) for cid in chunk_ids]

    @property
    def retrieval_top_k(self) -> int:
        """Return the configured top-k."""
        return self._top_k


def _make_minimal_pipeline():
    """Build a RAGPipeline with just enough wiring for chunk references."""
    from DashAI.back.models.RAG.RAG_pipeline import RAGPipeline, RAGPipelineConfig

    config = MagicMock(spec=RAGPipelineConfig)
    config.session_id = 1
    config.documents = [1]
    document = MagicMock()
    document.file_name = "doc.txt"
    return RAGPipeline(
        config=config,
        pipeline_id=1,
        chunking_model_id=1,
        documents={1: document},
        chunks={},
        prompt_model=MagicMock(),
        chunking_model=MagicMock(),
        retriever=MagicMock(),
        llm_model=MagicMock(),
    )


def test_chunk_ref_format_is_document_id_position():
    """The ref is exactly ``<document_id>_<position>``."""
    assert chunk_ref(_chunk(7, 3)) == "7_3"


def test_retriever_trace_node_shape():
    """A unit node has a name and chunk refs, and no children key."""
    retriever = _StubRetriever([_chunk(1, 0)], top_k=1)
    node = retriever_trace(retriever, [_chunk(1, 0)])

    assert node == {"name": "_StubRetriever", "chunks": ["1_0"]}
    assert "children" not in node


def test_retriever_trace_canonical_keys_cannot_be_overridden():
    """``name``/``chunks`` are canonical; extras may not shadow them.

    ``chunks`` cannot collide from callers at all (a positional binding raises
    a plain ``TypeError`` from Python, reachable only through a positional
    argument), so only the ``name``-via-``**extras`` spread path is covered.
    """
    stub = _StubRetriever([], top_k=1)
    with pytest.raises(ValueError, match="canonical"):
        retriever_trace(stub, [], name="_StubRetriever")


def test_trace_refs_are_the_pipeline_dict_keys():
    """The ref format is byte-identical to the pipeline's Dict row keys."""
    chunk = _chunk(1, 0)
    pipeline = _make_minimal_pipeline()

    _text, chunk_dict = pipeline._build_chunk_references([chunk])

    # Compare against the LITERAL format (not just the shared helper), so a
    # change to BOTH paths at once would still be caught here.
    assert set(chunk_dict) == {"1_0"}
    assert set(chunk_dict) == {chunk_ref(chunk)}


def test_parallel_trace_nests_children_in_query_order():
    """Parallel children nodes appear in child order and are always a list."""
    left = _StubRetriever([_chunk(1, 0)], top_k=1)
    right = _StubRetriever([_chunk(2, 1)], top_k=1)
    parallel = ParallelRetriever(children=[left, right], merge_strategy="round_robin")

    chunks, trace = parallel.retrieve("q")

    assert [chunk_ref(c) for c in chunks] == ["1_0", "2_1"]
    assert trace["name"] == "ParallelRetriever"
    assert [node["chunks"] for node in trace["children"]] == [["1_0"], ["2_1"]]


def test_sequential_trace_nests_first_child_node():
    """The cascade captures the (only) retrieving child, preserving order."""
    left = _StubRetriever([_chunk(1, 0)], top_k=1)
    right = _StubRetriever([_chunk(2, 0)], top_k=1)
    parallel = ParallelRetriever(children=[left, right], merge_strategy="round_robin")
    reranker = _StubRetriever([], top_k=1)
    sequential = SequentialRetriever(children=[parallel, reranker])

    chunks, trace = sequential.retrieve("q")

    assert trace["name"] == "SequentialRetriever"
    assert len(trace["children"]) == 1
    first_node = trace["children"][0]
    assert first_node["name"] == "ParallelRetriever"
    assert [node["chunks"] for node in first_node["children"]] == [["1_0"], ["2_0"]]
    assert trace["chunks"] == [chunk_ref(c) for c in chunks]
