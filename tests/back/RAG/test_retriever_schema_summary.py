"""Tests for the retriever schema-summary contract."""

from __future__ import annotations

import json
from types import SimpleNamespace
from typing import Dict, List, Tuple

from DashAI.back.models.RAG.documents import Chunk
from DashAI.back.models.RAG.retrievers.base_retriever import BaseRetriever
from DashAI.back.models.RAG.retrievers.composite.parallel_retriever import (
    ParallelRetriever,
)
from DashAI.back.models.RAG.retrievers.dense.dense_embedding_retriever import (
    DenseEmbeddingRetriever,
)
from DashAI.back.models.RAG.retrievers.sparse.bm25_retriever import BM25Retriever
from DashAI.back.models.RAG.retrievers.sparse.tfidf_retriever import TFIDFRetriever


def test_base_retriever_declares_no_schema_summary_parameters():
    """The abstract base exposes no schema-summary metadata."""
    assert BaseRetriever.get_schema_summary_parameters() == {}
    assert "schema_summary_parameters" not in BaseRetriever.get_metadata()


def test_bm25_metadata_exposes_schema_summary_parameters():
    """BM25 publishes the k1/b/top-k display labels and dotted paths."""
    assert BM25Retriever.get_metadata()["schema_summary_parameters"] == {
        "k1": "k1",
        "b": "b",
        "top_k": "top_k",
    }


def test_dense_embedding_metadata_exposes_nested_parameter_path():
    """The dense embedding retriever points at the nested embedding model."""
    assert DenseEmbeddingRetriever.get_metadata()["schema_summary_parameters"] == {
        "embedding_model": "embedding_model.model_name",
        "similarity_metric": "similarity_metric",
        "top_k": "top_k",
    }


class _Unit(BaseRetriever):
    """Minimal unit retriever with a top-k summary parameter."""

    @classmethod
    def _get_main_parameters(cls) -> Dict[str, str]:
        return {"top_k": "top_k"}

    def retrieve(self, query, **kwargs) -> Tuple[List[Chunk], Dict[str, object]]:
        return [], {}

    def score_chunks(self, chunk_ids, query):
        return []

    @property
    def retrieval_top_k(self) -> int:
        return 5


def test_unit_summary_resolves_params_and_omits_children():
    """A unit summary resolves its path and has no ``children`` key."""
    retriever = _Unit(top_k=5)

    summary = retriever.get_schema_summary()

    assert summary == {"class": "_Unit", "params": {"top_k": 5}}
    assert json.dumps(summary)


def test_nested_component_path_is_resolved():
    """A dotted path descends into component-ref ``params``."""

    class _Nested(BaseRetriever):
        @classmethod
        def _get_main_parameters(cls) -> Dict[str, str]:
            return {"embedding_model": "embedding_model.model_name"}

        def retrieve(self, query, **kwargs):
            return [], {}

        def score_chunks(self, chunk_ids, query):
            return []

    retriever = _Nested(
        embedding_model={
            "component": "SentenceTransformerEmbedding",
            "params": {"model_name": "demo-model"},
        }
    )

    assert retriever.get_schema_summary()["params"] == {"embedding_model": "demo-model"}


def test_nested_path_resolves_from_factory_trace_params():
    """A factory snapshot resolves nested component-ref parameters."""

    class _FactoryNested(BaseRetriever):
        @classmethod
        def _get_main_parameters(cls) -> Dict[str, str]:
            return {"embedding_model": "embedding_model.model_name"}

        def retrieve(self, query, **kwargs):
            return [], {}

        def score_chunks(self, chunk_ids, query):
            return []

    retriever = _FactoryNested()
    retriever.set_trace_params(
        {
            "embedding_model": {
                "component": "SentenceTransformerEmbedding",
                "params": {"model_name": "trace-model"},
            }
        }
    )

    assert retriever.get_schema_summary()["params"] == {
        "embedding_model": "trace-model"
    }


def test_unresolvable_path_is_omitted():
    """A path that cannot be resolved is omitted instead of emitted as None."""

    class _Missing(BaseRetriever):
        @classmethod
        def _get_main_parameters(cls) -> Dict[str, str]:
            return {"missing": "does.not.exist", "top_k": "top_k"}

        def retrieve(self, query, **kwargs):
            return [], {}

        def score_chunks(self, chunk_ids, query):
            return []

    summary = _Missing(top_k=3).get_schema_summary()

    assert summary["params"] == {"top_k": 3}


def test_direct_bm25_summary_includes_top_k():
    """Directly constructed BM25 resolves its weighting and top-k paths."""
    retriever = BM25Retriever(
        BM25Vectorizer=SimpleNamespace(vectorizer=object()),
        k1=1.5,
        b=0.75,
        delta=0.0,
        similarity_function="cosine",
        top_k=5,
    )

    summary = retriever.get_schema_summary()

    assert summary["params"] == {"k1": 1.5, "b": 0.75, "top_k": 5}


def test_direct_tfidf_summary_resolves_similarity_and_top_k():
    """Directly constructed TF-IDF resolves both summary paths."""
    vectorizer = SimpleNamespace(model=object())
    retriever = TFIDFRetriever(
        TFIDFVectorizer=vectorizer,
        similarity_function="cosine",
        top_k=7,
    )

    summary = retriever.get_schema_summary()

    assert summary["params"] == {"similarity_function": "cosine", "top_k": 7}


def test_direct_dense_embedding_summary_resolves_nested_and_top_k():
    """Directly constructed dense embedding resolves the nested model path."""
    embedding = SimpleNamespace(params={"model_name": "demo-model"})
    retriever = DenseEmbeddingRetriever(
        embedding_model=embedding,
        similarity_metric="cosine",
        top_k=3,
    )

    summary = retriever.get_schema_summary()

    assert summary["params"] == {
        "embedding_model": "demo-model",
        "similarity_metric": "cosine",
        "top_k": 3,
    }


def test_composite_summary_recurses_and_serializes_enums():
    """A composite nests child summaries and converts enum values."""
    parallel = ParallelRetriever(
        children=[_Unit(top_k=1), _Unit(top_k=2)], merge_strategy="round_robin"
    )

    summary = parallel.get_schema_summary()

    assert summary["class"] == "ParallelRetriever"
    assert summary["params"] == {"merge_strategy": "round_robin"}
    assert [child["class"] for child in summary["children"]] == ["_Unit", "_Unit"]
    assert summary["children"][1]["params"] == {"top_k": 2}
    assert json.dumps(summary)
