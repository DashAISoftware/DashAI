"""Centralized RAG backend defaults.

This module is the single source of truth for the backend defaults shared by
the retriever presets, the RAG session defaults and the placeholders of the
LLM-evaluated composite retrievers:

* the default keyword, semantic and hybrid retrievers,
* the default semantic embedding model,
* the default RAG function-calling LLM (the registered Qwen 2.5 1.5B, with
  the context window RAG retrieval evaluation needs).

The recipes are expressed as plain ``{component, params}`` dictionaries with
component names as strings, so this module never imports component classes and
cannot introduce import cycles. Every factory returns a fresh dictionary:
callers can mutate the result without affecting a later call or another
caller.
"""

import copy
import math
from typing import Any, Dict

#: Number of chunks the default retrievers select.
DEFAULT_TOP_K = 10

#: Small multilingual Sentence Transformer used by the semantic default.
DEFAULT_SEMANTIC_MODEL_NAME = (
    "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
)

#: Context window the default RAG function-calling LLM needs to judge a
#: retrieval pool together with the sufficiency prompt. Shared with the
#: session-level generation budget so both cannot drift apart.
DEFAULT_RAG_CONTEXT_WINDOW = 10_000
DEFAULT_FUNCTION_CALLING_LLM_CONTEXT_WINDOW = DEFAULT_RAG_CONTEXT_WINDOW

#: Default pool and round budgets for the LLM-evaluated retrievers.
DEFAULT_MAX_CHUNKS = 10
DEFAULT_MAX_ITERS = 3

#: Default maximum number of function-call attempts (first call included).
DEFAULT_FUNCTION_CALL_MAX_TRIALS = 3

#: Upper bound for the configurable function-call attempts, so a typo cannot
#: turn a single RAG turn into an effectively unbounded LLM retry loop.
MAX_FUNCTION_CALL_TRIALS = 10

#: Default retrieval-sufficiency prompt component.
DEFAULT_SUFFICIENCY_PROMPT_COMPONENT = "DefaultRetrievalSufficiencyPrompt"

#: Component names used by the recipes.
KEYWORD_RETRIEVER_COMPONENT = "BM25Retriever"
SEMANTIC_RETRIEVER_COMPONENT = "DenseEmbeddingRetriever"
HYBRID_RETRIEVER_COMPONENT = "ParallelRetriever"
FUNCTION_CALLING_LLM_COMPONENT = "Qwen25_15BInstruct"
BM25_VECTORIZER_COMPONENT = "BM25VectorizerModel"
SENTENCE_TRANSFORMER_EMBEDDING_COMPONENT = "SentenceTransformerEmbedding"

#: Complete BM25 vectorizer parameters (the schema fills no missing values).
_BM25_VECTORIZER_PARAMS: Dict[str, Any] = {
    "strip_accents": None,
    "lowercase": True,
    "stop_words": None,
    "max_df": 1.0,
    "min_df": 0.0,
    "max_features": None,
}

#: Complete keyword retriever parameters, before applying ``top_k``.
_KEYWORD_PARAMS: Dict[str, Any] = {
    "BM25Vectorizer": {
        "component": BM25_VECTORIZER_COMPONENT,
        "params": _BM25_VECTORIZER_PARAMS,
    },
    "k1": 1.5,
    "b": 0.75,
    "delta": 0.0,
    "similarity_function": "cosine",
    "top_k": DEFAULT_TOP_K,
}

#: Complete semantic retriever parameters, before applying ``top_k``.
_SEMANTIC_PARAMS: Dict[str, Any] = {
    "embedding_model": {
        "component": SENTENCE_TRANSFORMER_EMBEDDING_COMPONENT,
        "params": {
            "model_name": DEFAULT_SEMANTIC_MODEL_NAME,
            "overflow_strategy": "truncate",
            "normalize": True,
            "device": "cpu",
        },
    },
    "similarity_metric": "cosine",
    "top_k": DEFAULT_TOP_K,
}

#: Complete RAG function-calling LLM parameters.
_FUNCTION_CALLING_LLM_PARAMS: Dict[str, Any] = {
    "max_tokens": 100,
    "temperature": 0.7,
    "frequency_penalty": 0.1,
    "context_window": DEFAULT_FUNCTION_CALLING_LLM_CONTEXT_WINDOW,
    "device": "CPU",
}


def default_keyword_retriever(top_k: int = DEFAULT_TOP_K) -> Dict[str, Any]:
    """Return the default keyword (BM25) retriever recipe.

    Parameters
    ----------
    top_k : int, optional
        Number of chunks the retriever selects. Defaults to
        :data:`DEFAULT_TOP_K`.

    Returns
    -------
    Dict[str, Any]
        A fresh ``{"component": "BM25Retriever", "params": {...}}`` reference
        with every schema parameter populated.
    """
    params = copy.deepcopy(_KEYWORD_PARAMS)
    params["top_k"] = top_k
    return {"component": KEYWORD_RETRIEVER_COMPONENT, "params": params}


def default_semantic_retriever(top_k: int = DEFAULT_TOP_K) -> Dict[str, Any]:
    """Return the default semantic (dense embedding) retriever recipe.

    Parameters
    ----------
    top_k : int, optional
        Number of chunks the retriever selects. Defaults to
        :data:`DEFAULT_TOP_K`.

    Returns
    -------
    Dict[str, Any]
        A fresh ``{"component": "DenseEmbeddingRetriever", "params": {...}}``
        reference using :data:`DEFAULT_SEMANTIC_MODEL_NAME`.
    """
    params = copy.deepcopy(_SEMANTIC_PARAMS)
    params["top_k"] = top_k
    return {"component": SEMANTIC_RETRIEVER_COMPONENT, "params": params}


def default_hybrid_retriever(top_k: int = DEFAULT_TOP_K) -> Dict[str, Any]:
    """Return the default hybrid retriever recipe.

    The hybrid is a ``ParallelRetriever`` that round-robins the keyword and
    semantic defaults. The budget is split with ``ceil`` for keyword retrieval
    and ``floor`` for semantic retrieval, so the children add up to ``top_k``.

    Parameters
    ----------
    top_k : int, optional
        Total number of chunks the hybrid retriever returns. Defaults to
        :data:`DEFAULT_TOP_K`.

    Returns
    -------
    Dict[str, Any]
        A fresh ``{"component": "ParallelRetriever", "params": {...}}``
        reference with fully configured children.
    """
    # Each child must keep a valid positive top_k. With top_k=1 the raw split
    # would give the semantic child 0, which its schema rejects; the endpoint
    # accepts top_k>=1, so clamp both branches.
    keyword_top_k = max(1, math.ceil(top_k / 2))
    semantic_top_k = max(1, math.floor(top_k / 2))
    return {
        "component": HYBRID_RETRIEVER_COMPONENT,
        "params": {
            "merge_strategy": "round_robin",
            "children": [
                default_keyword_retriever(keyword_top_k),
                default_semantic_retriever(semantic_top_k),
            ],
        },
    }


def default_retrieval_sufficiency_prompt() -> Dict[str, Any]:
    """Return the default retrieval-sufficiency prompt reference.

    Returns
    -------
    Dict[str, Any]
        A fresh
        ``{"component": "DefaultRetrievalSufficiencyPrompt", "params": {}}``
        reference. The backend injects the language template.
    """
    return {
        "component": DEFAULT_SUFFICIENCY_PROMPT_COMPONENT,
        "params": {},
    }


def default_function_calling_llm() -> Dict[str, Any]:
    """Return the default RAG function-calling LLM recipe.

    The default is the registered Qwen 2.5 1.5B Instruct component. Its schema
    ships a conservative 512-token context window; the RAG default overrides it
    to :data:`DEFAULT_FUNCTION_CALLING_LLM_CONTEXT_WINDOW` because retrieval
    evaluation needs to fit the sufficiency prompt plus the retrieved chunks in
    one pass.

    Returns
    -------
    Dict[str, Any]
        A fresh ``{"component": "Qwen25_15BInstruct", "params": {...}}``
        reference using the RAG context window.
    """
    return {
        "component": FUNCTION_CALLING_LLM_COMPONENT,
        "params": copy.deepcopy(_FUNCTION_CALLING_LLM_PARAMS),
    }
