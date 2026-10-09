"""Retriever exception classes — re-exported from the unified RAG hierarchy.

All RAG exception types are defined in
:mod:`DashAI.back.models.RAG.exceptions` to avoid circular imports
and provide a single source of truth.  This module re-exports the
retriever-specific subset for convenience.
"""

from DashAI.back.models.RAG.exceptions import (
    RAGRetrieverCompositeValidationError as CompositeValidationError,
)
from DashAI.back.models.RAG.exceptions import (
    RAGRetrieverError as RetrieverError,
)
from DashAI.back.models.RAG.exceptions import (
    RAGRetrieverMissingParameterError as MissingParameterError,
)

__all__ = [
    "CompositeValidationError",
    "MissingParameterError",
    "RetrieverError",
]
