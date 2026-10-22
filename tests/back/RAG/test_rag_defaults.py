"""Tests for the centralized RAG backend defaults.

The defaults module is the single source of truth for the retriever preset
identities and parameters, the default RAG function-calling LLM, and the
placeholders of the LLM-evaluated composite retrievers.
"""

from __future__ import annotations

import ast
import inspect
from typing import Any, Dict

from DashAI.back.initial_components import get_initial_components
from DashAI.back.models.hugging_face.qwen_model import Qwen25_15BInstruct
from DashAI.back.models.RAG.embeddings.dense.sentence_transformer_embedding import (
    SentenceTransformerEmbedding,
)
from DashAI.back.models.RAG.RAG_defaults import (
    DEFAULT_FUNCTION_CALL_MAX_TRIALS,
    DEFAULT_FUNCTION_CALLING_LLM_CONTEXT_WINDOW,
    DEFAULT_MAX_CHUNKS,
    DEFAULT_MAX_ITERS,
    DEFAULT_SEMANTIC_MODEL_NAME,
    DEFAULT_TOP_K,
    default_function_calling_llm,
    default_hybrid_retriever,
    default_keyword_retriever,
    default_retrieval_sufficiency_prompt,
    default_semantic_retriever,
)
from DashAI.back.models.RAG.retrievers.composite.llm_evaluated_depth_retriever import (
    LLMEvaluatedDepthRetriever,
)
from DashAI.back.models.RAG.retrievers.composite.llm_evaluated_ensemble_retriever import (  # noqa: E501
    LLMEvaluatedEnsembleRetriever,
)
from DashAI.back.models.RAG.retrievers.composite.parallel_retriever import (
    ParallelRetriever,
)
from DashAI.back.models.RAG.retrievers.dense.dense_embedding_retriever import (
    DenseEmbeddingRetriever,
)
from DashAI.back.models.RAG.retrievers.sparse.bm25_retriever import (
    BM25Retriever,
    BM25VectorizerModel,
)

# ---------------------------------------------------------------------------
# retriever factories
# ---------------------------------------------------------------------------


class TestRetrieverFactories:
    """The keyword, semantic and hybrid recipes are centralized and complete."""

    def test_default_keyword_retriever(self):
        ref = default_keyword_retriever()

        assert ref["component"] == "BM25Retriever"
        params = ref["params"]
        assert params["top_k"] == DEFAULT_TOP_K
        assert params["k1"] == 1.5
        assert params["b"] == 0.75
        assert params["delta"] == 0.0
        assert params["similarity_function"] == "cosine"

        vectorizer = params["BM25Vectorizer"]
        assert vectorizer["component"] == "BM25VectorizerModel"
        assert vectorizer["params"] == {
            "strip_accents": None,
            "lowercase": True,
            "stop_words": None,
            "max_df": 1.0,
            "min_df": 0.0,
            "max_features": None,
        }

    def test_default_keyword_retriever_custom_top_k(self):
        ref = default_keyword_retriever(top_k=3)

        assert ref["params"]["top_k"] == 3

    def test_default_semantic_retriever(self):
        ref = default_semantic_retriever()

        assert ref["component"] == "DenseEmbeddingRetriever"
        params = ref["params"]
        assert params["top_k"] == DEFAULT_TOP_K
        assert params["similarity_metric"] == "cosine"

        embedding = params["embedding_model"]
        assert embedding["component"] == "SentenceTransformerEmbedding"
        assert embedding["params"] == {
            "model_name": DEFAULT_SEMANTIC_MODEL_NAME,
            "overflow_strategy": "truncate",
            "normalize": True,
            "device": "cpu",
        }
        assert DEFAULT_SEMANTIC_MODEL_NAME == (
            "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
        )

    def test_default_hybrid_retriever_splits_top_k(self):
        ref = default_hybrid_retriever(top_k=15)

        assert ref["component"] == "ParallelRetriever"
        params = ref["params"]
        assert params["merge_strategy"] == "round_robin"

        keyword, semantic = params["children"]
        assert keyword["component"] == "BM25Retriever"
        assert keyword["params"]["top_k"] == 8  # ceil(15 / 2)
        assert semantic["component"] == "DenseEmbeddingRetriever"
        assert semantic["params"]["top_k"] == 7  # floor(15 / 2)

    def test_default_hybrid_retriever_defaults_to_ten(self):
        ref = default_hybrid_retriever()

        keyword, semantic = ref["params"]["children"]
        assert keyword["params"]["top_k"] == 5
        assert semantic["params"]["top_k"] == 5

    def test_default_hybrid_retriever_keeps_small_top_k_valid(self):
        ref = default_hybrid_retriever(top_k=1)

        keyword, semantic = ref["params"]["children"]
        assert keyword["params"]["top_k"] == 1
        assert semantic["params"]["top_k"] == 1

    def test_factories_return_fresh_dicts(self):
        first = default_keyword_retriever()
        first["params"]["top_k"] = 999
        first["params"]["BM25Vectorizer"]["params"]["lowercase"] = False
        assert default_keyword_retriever()["params"]["top_k"] == DEFAULT_TOP_K
        assert (
            default_keyword_retriever()["params"]["BM25Vectorizer"]["params"][
                "lowercase"
            ]
            is True
        )

        semantic = default_semantic_retriever()
        semantic["params"]["embedding_model"]["params"]["device"] = "cuda"
        assert (
            default_semantic_retriever()["params"]["embedding_model"]["params"][
                "device"
            ]
            == "cpu"
        )

        hybrid = default_hybrid_retriever()
        hybrid["params"]["children"][0]["params"]["top_k"] = 999
        assert (
            default_hybrid_retriever()["params"]["children"][0]["params"]["top_k"] == 5
        )

        llm = default_function_calling_llm()
        llm["params"]["context_window"] = 1
        assert (
            default_function_calling_llm()["params"]["context_window"]
            == DEFAULT_FUNCTION_CALLING_LLM_CONTEXT_WINDOW
        )


# ---------------------------------------------------------------------------
# default function-calling LLM
# ---------------------------------------------------------------------------


class TestDefaultFunctionCallingLLM:
    """The default RAG LLM is a complete, valid Qwen 1.5B recipe."""

    def test_default_function_calling_llm(self):
        ref = default_function_calling_llm()

        assert ref["component"] == "Qwen25_15BInstruct"
        assert ref["params"] == {
            "max_tokens": 100,
            "temperature": 0.7,
            "frequency_penalty": 0.1,
            "context_window": DEFAULT_FUNCTION_CALLING_LLM_CONTEXT_WINDOW,
            "device": "CPU",
        }
        assert DEFAULT_FUNCTION_CALLING_LLM_CONTEXT_WINDOW == 10_000

    def test_default_llm_overrides_the_qwen_context_window(self):
        """The registered Qwen keeps its schema default; RAG overrides it."""
        schema = Qwen25_15BInstruct.get_schema()
        assert schema["properties"]["context_window"]["placeholder"] == 512

        ref = default_function_calling_llm()
        assert ref["params"]["context_window"] == 10_000
        Qwen25_15BInstruct.SCHEMA.model_validate(ref["params"])

    def test_qwen_supports_function_calling(self):
        assert Qwen25_15BInstruct.supports_function_calling() is True

    def test_default_params_validate_against_their_schemas(self):
        keyword = default_keyword_retriever()
        semantic = default_semantic_retriever()
        BM25Retriever.SCHEMA.model_validate(keyword["params"])
        DenseEmbeddingRetriever.SCHEMA.model_validate(semantic["params"])
        ParallelRetriever.SCHEMA.model_validate(default_hybrid_retriever()["params"])
        Qwen25_15BInstruct.SCHEMA.model_validate(
            default_function_calling_llm()["params"]
        )

        # component_field only validates the {component, params} container, so
        # the nested schemas need their own check.
        BM25VectorizerModel.SCHEMA.model_validate(
            keyword["params"]["BM25Vectorizer"]["params"]
        )
        SentenceTransformerEmbedding.SCHEMA.model_validate(
            semantic["params"]["embedding_model"]["params"]
        )

    def test_default_llm_component_is_registered(self):
        registered = {component.__name__ for component in get_initial_components()}
        assert "Qwen25_15BInstruct" in registered

    def test_default_llm_params_cover_every_schema_field(self):
        validated = Qwen25_15BInstruct.SCHEMA.model_validate(
            default_function_calling_llm()["params"]
        )
        assert set(validated.model_dump()) == {
            "max_tokens",
            "temperature",
            "frequency_penalty",
            "context_window",
            "device",
        }


# ---------------------------------------------------------------------------
# LLM-evaluated retriever placeholders
# ---------------------------------------------------------------------------


class TestLLMEvaluatedRetrieverPlaceholders:
    """The adaptive retrievers seed their component fields with the defaults."""

    def _placeholder(self, component: Any, field: str) -> Dict[str, Any]:
        return component.get_schema()["properties"][field]["placeholder"]

    def test_depth_retriever_placeholders(self):
        assert self._placeholder(LLMEvaluatedDepthRetriever, "children") == [
            default_hybrid_retriever()
        ]
        assert (
            self._placeholder(LLMEvaluatedDepthRetriever, "llm_model")
            == default_function_calling_llm()
        )
        assert (
            self._placeholder(LLMEvaluatedDepthRetriever, "prompt")
            == default_retrieval_sufficiency_prompt()
        )
        assert (
            self._placeholder(LLMEvaluatedDepthRetriever, "max_chunks")
            == DEFAULT_MAX_CHUNKS
        )
        assert (
            self._placeholder(LLMEvaluatedDepthRetriever, "max_iters")
            == DEFAULT_MAX_ITERS
        )
        assert (
            self._placeholder(LLMEvaluatedDepthRetriever, "function_call_max_trials")
            == DEFAULT_FUNCTION_CALL_MAX_TRIALS
        )

    def test_ensemble_retriever_placeholders(self):
        assert self._placeholder(LLMEvaluatedEnsembleRetriever, "children") == [
            default_semantic_retriever(),
            default_keyword_retriever(),
        ]
        assert (
            self._placeholder(LLMEvaluatedEnsembleRetriever, "llm_model")
            == default_function_calling_llm()
        )
        assert (
            self._placeholder(LLMEvaluatedEnsembleRetriever, "prompt")
            == default_retrieval_sufficiency_prompt()
        )
        assert (
            self._placeholder(LLMEvaluatedEnsembleRetriever, "max_chunks")
            == DEFAULT_MAX_CHUNKS
        )
        assert (
            self._placeholder(LLMEvaluatedEnsembleRetriever, "max_iters")
            == DEFAULT_MAX_ITERS
        )
        assert (
            self._placeholder(LLMEvaluatedEnsembleRetriever, "function_call_max_trials")
            == DEFAULT_FUNCTION_CALL_MAX_TRIALS
        )

    def test_placeholders_are_independent_copies(self):
        depth_schema = LLMEvaluatedDepthRetriever.get_schema()
        depth_schema["properties"]["children"]["placeholder"][0]["params"][
            "merge_strategy"
        ] = "interleave"

        assert self._placeholder(LLMEvaluatedDepthRetriever, "children") == [
            default_hybrid_retriever()
        ]


def test_defaults_module_only_imports_the_standard_library():
    """The defaults module cannot create import cycles with component classes."""
    import DashAI.back.models.RAG.RAG_defaults as module

    tree = ast.parse(inspect.getsource(module))
    imported = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            imported.append(node.module or "")
        elif isinstance(node, ast.Import):
            imported.extend(alias.name for alias in node.names)
    assert not any(name.startswith("DashAI") for name in imported)
