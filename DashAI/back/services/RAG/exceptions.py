"""Service-layer RAG exceptions.

Re-exports exception types from the unified RAG exception hierarchy
(:mod:`DashAI.back.models.RAG.exceptions`) so that service-layer code
does not import directly from the models layer.

All RAG exception types are defined in a single hierarchy under
:mod:`DashAI.back.models.RAG.exceptions`.  This module re-exports
the subset needed by services.
"""

from DashAI.back.models.RAG.exceptions import (  # noqa: F401
    RAGDatabaseError,
    RAGPromptValidationError,
)

__all__ = [
    "RAGDatabaseError",
    "RAGPromptValidationError",
]
