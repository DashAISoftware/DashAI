"""Canonical RAG pipeline parameter keys.
Single source of truth shared across models, services, and API layers.
Also covers composite retriever names.
"""

RAG_PARAM_DOCUMENTS = "documents"
RAG_PARAM_PROMPT = "prompt"
RAG_PARAM_CHUNKING_MODEL = "chunking_model"
RAG_PARAM_RETRIEVER_MODEL = "retriever_model"
RAG_PARAM_GENERATION_MODEL = "generation_model"

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

# Infrastructure / internal keys (not user-visible components)
ENV_RAG_PATH = "env_RAG_path"

RAG_INFRA_KEYS = frozenset({"session_id", "db", "component_registry", ENV_RAG_PATH})

# All known pipeline keys combined (for the "unknown keys" guard)
RAG_PARAM_KEYS_ALL = frozenset(RAG_INFRA_KEYS | RAG_PARAM_KEYS | set(RAG_MODEL_KEYS))

COMPOSITE_RETRIEVER_NAMES = frozenset(
    {
        "SequentialRetriever",
        "ParallelRetriever",
        "MMRRerankerRetriever",
        "SentenceTransformerCrossEncoderRetriever",
    }
)
