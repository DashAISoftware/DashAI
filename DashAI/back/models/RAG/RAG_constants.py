"""Canonical RAG pipeline parameter keys.
Single source of truth shared across models, services, and API layers.
Also covers composite retriever names.

Output rows
-----------
A finished RAG process emits four typed ``ProcessData`` output rows
(``is_input=False``) in pipeline-chronological order:

1. ``Queries`` — the JSON list of queries used for retrieval. Always emitted;
   when the query transformation stage is disabled the list is the
   one-element ``[input_message]``.
2. ``Dict`` — the JSON map ``{ref: chunk_info}`` of retrieved chunks.
3. ``Trace`` — the JSON list of per-query retrieval trace nodes. Trace chunk
   references use the SAME ``"<document_id>_<position>"`` keys as ``Dict``.
4. ``str`` — the LLM answer message.
"""

RAG_PARAM_DOCUMENTS = "documents"
RAG_PARAM_PROMPT = "prompt"
RAG_PARAM_CHUNKING_MODEL = "chunking_model"
RAG_PARAM_RETRIEVER_MODEL = "retriever_model"
RAG_PARAM_GENERATION_MODEL = "generation_model"
RAG_PARAM_QUERY_TRANSFORMATION = "query_transformation"

# All known RAG pipeline parameter keys
RAG_PARAM_KEYS = frozenset(
    {
        RAG_PARAM_DOCUMENTS,
        RAG_PARAM_PROMPT,
        RAG_PARAM_CHUNKING_MODEL,
        RAG_PARAM_RETRIEVER_MODEL,
        RAG_PARAM_GENERATION_MODEL,
    }
)

# Model component keys (each has {component, params} structure)
RAG_MODEL_KEYS = (
    RAG_PARAM_PROMPT,
    RAG_PARAM_CHUNKING_MODEL,
    RAG_PARAM_RETRIEVER_MODEL,
    RAG_PARAM_GENERATION_MODEL,
)

# Optional model component keys (model-key shaped but not required)
RAG_OPTIONAL_MODEL_KEYS = (RAG_PARAM_QUERY_TRANSFORMATION,)

# ProcessData ``data_type`` values of the four output rows, in the order the
# task emits them: Queries → Dict (chunks) → Trace → str (message).
RAG_OUTPUT_QUERIES_TYPE = "Queries"
RAG_OUTPUT_CHUNKS_TYPE = "Dict"
RAG_OUTPUT_TRACE_TYPE = "Trace"
RAG_OUTPUT_MESSAGE_TYPE = "str"

# Infrastructure / internal keys (not user-visible components)
ENV_RAG_PATH = "env_RAG_path"

RAG_INFRA_KEYS = frozenset({"session_id", "db", "component_registry", ENV_RAG_PATH})

# All known pipeline keys combined (for the "unknown keys" guard)
RAG_PARAM_KEYS_ALL = frozenset(
    RAG_INFRA_KEYS | RAG_PARAM_KEYS | set(RAG_MODEL_KEYS) | set(RAG_OPTIONAL_MODEL_KEYS)
)

COMPOSITE_RETRIEVER_NAMES = frozenset(
    {
        "SequentialRetriever",
        "ParallelRetriever",
        "MMRRerankerRetriever",
        "SentenceTransformerCrossEncoderRetriever",
        "LLMEvaluatedDepthRetriever",
        "LLMEvaluatedEnsembleRetriever",
    }
)

#: Composite retrievers that consult an LLM to judge retrieval sufficiency.
#: Shared by the retriever evaluation validation service (and any future caller
#: that needs to special-case the LLM-evaluated family).
LLM_EVALUATED_RETRIEVER_NAMES = frozenset(
    {
        "LLMEvaluatedDepthRetriever",
        "LLMEvaluatedEnsembleRetriever",
    }
)
