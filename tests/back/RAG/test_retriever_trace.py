"""Unit tests for the retriever trace contract.

Every ``retrieve()`` returns ``(chunks, trace)``. These tests pin the trace
node shape, the single-source chunk reference format, and the nesting of
composite children.
"""

from __future__ import annotations

import json
from typing import Dict, List, Tuple
from unittest.mock import MagicMock

import pytest

from DashAI.back.core.utils import MultilingualString
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


class _DescribedRetriever(_StubRetriever):
    """Stub declaring its own description and representation template."""

    DESCRIPTION = MultilingualString(
        en="Described retriever.",
        es="Recuperador descrito.",
    )
    REPRESENTATION = MultilingualString(
        en="top-k {top_k} · {child.model_name}",
        es="top-k {top_k} · {child.model_name}",
    )


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
    """A unit node has a name, chunk refs and a schema summary."""
    retriever = _StubRetriever([_chunk(1, 0)], top_k=1)
    node = retriever_trace(retriever, [_chunk(1, 0)])

    assert node == {
        "name": "_StubRetriever",
        "chunks": ["1_0"],
        "schema_summary": {"class": "_StubRetriever", "params": {}},
    }
    assert "children" not in node


def test_retriever_trace_omits_schema_summary_when_it_raises():
    """A broken schema summary is omitted instead of breaking the trace."""

    class _BrokenSummaryRetriever(_StubRetriever):
        def get_schema_summary(self):
            raise RuntimeError("broken summary")

    retriever = _BrokenSummaryRetriever([], top_k=1)
    node = retriever_trace(retriever, [])

    assert "schema_summary" not in node
    assert node["name"] == "_BrokenSummaryRetriever"


def test_retriever_trace_canonical_schema_summary_cannot_be_overridden():
    """Extras may not shadow the schema summary."""
    stub = _StubRetriever([], top_k=1)
    with pytest.raises(ValueError, match="canonical"):
        retriever_trace(stub, [], schema_summary={"class": "nope"})


def test_retriever_trace_canonical_keys_cannot_be_overridden():
    """``name``/``chunks`` are canonical; extras may not shadow them.

    ``chunks`` cannot collide from callers at all (a positional binding raises
    a plain ``TypeError`` from Python, reachable only through a positional
    argument), so only the ``name``-via-``**extras`` spread path is covered.
    """
    stub = _StubRetriever([], top_k=1)
    with pytest.raises(ValueError, match="canonical"):
        retriever_trace(stub, [], name="_StubRetriever")


def test_retriever_trace_includes_description_and_representation():
    """A described/represented retriever emits localized dicts and stays JSON."""
    retriever = _DescribedRetriever([_chunk(1, 0)], top_k=1)
    retriever.set_trace_params(
        {
            "top_k": 3,
            "child": {"component": "ChildRetriever", "params": {"model_name": "demo"}},
        }
    )

    node = retriever_trace(retriever, [_chunk(1, 0)])

    assert node["description"] == {
        "en": "Described retriever.",
        "es": "Recuperador descrito.",
    }
    assert node["representation"] == {
        "en": "top-k 3 · demo",
        "es": "top-k 3 · demo",
    }
    assert node["chunks"] == ["1_0"]
    assert json.dumps(node)


def test_retriever_trace_omits_unresolved_representation():
    """No trace params means every placeholder misses, so no representation."""
    retriever = _DescribedRetriever([], top_k=1)

    node = retriever_trace(retriever, [])

    assert "representation" not in node
    assert node["description"] == {
        "en": "Described retriever.",
        "es": "Recuperador descrito.",
    }


def test_retriever_trace_canonical_description_cannot_be_overridden():
    """Extras may not shadow the rendered ``description``."""
    stub = _DescribedRetriever([], top_k=1)
    with pytest.raises(ValueError, match="canonical"):
        retriever_trace(stub, [], description={"en": "nope"})


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
