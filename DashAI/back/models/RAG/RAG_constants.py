"""Canonical RAG pipeline parameter keys.
Single source of truth shared across models, services, and API layers.
Also covers composite retriever names.

Output rows
-----------
A finished RAG process emits five typed ``ProcessData`` output rows
(``is_input=False``) in pipeline-chronological order:

1. ``Queries`` — the JSON list of queries used for retrieval. Always emitted;
   when the query transformation stage is disabled the list is the
   one-element ``[input_message]``.
2. ``Dict`` — the JSON map ``{ref: chunk_info}`` of retrieved chunks.
3. ``Trace`` — the JSON list of per-query retrieval trace nodes. Trace chunk
   references use the SAME ``"<document_id>_<position>"`` keys as ``Dict``.
4. ``Timings`` — the JSON object of per-stage wall-clock milliseconds
   (``transformation_ms``, ``retrieval_ms``, ``generation_ms``, ``total_ms``).
5. ``str`` — the LLM answer message.
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

# ProcessData ``data_type`` values of the five output rows, in the order the
# task emits them: Queries → Dict (chunks) → Trace → Timings → str (message).
RAG_OUTPUT_QUERIES_TYPE = "Queries"
RAG_OUTPUT_CHUNKS_TYPE = "Dict"
RAG_OUTPUT_TRACE_TYPE = "Trace"
RAG_OUTPUT_TIMINGS_TYPE = "Timings"
RAG_OUTPUT_MESSAGE_TYPE = "str"

# Live stage progress
# -------------------
# While a RAG process runs, ``GenerativeProcess.progress`` holds exactly one of
# these payloads so the chat frontend can show the current stage:
#
# - ``{"stage": "transforming"}`` — emitted only when the query transformation
#   stage is enabled, before the transformer runs.
# - ``{"stage": "retrieving", "queries": ["q1", "q2"]}`` — emitted after the
#   queries are resolved; ``queries`` is the resolved list actually retrieved.
# - ``{"stage": "generating"}`` — emitted after the queries are resolved and
#   before the prompt is built, so the reporter's own overhead is not charged
#   to the generation stage timing.
#
# The column is set back to ``None`` when the process finishes or errors.
RAG_PROGRESS_STAGE_KEY = "stage"
RAG_PROGRESS_QUERIES_KEY = "queries"
RAG_PROGRESS_STAGE_TRANSFORMING = "transforming"
RAG_PROGRESS_STAGE_RETRIEVING = "retrieving"
RAG_PROGRESS_STAGE_GENERATING = "generating"

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
    }
)
