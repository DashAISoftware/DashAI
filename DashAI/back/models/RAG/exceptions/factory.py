"""Factory-related RAG exceptions."""

from DashAI.back.models.RAG.exceptions.base import RAGWorkflowError


class RAGFactoryError(RAGWorkflowError):
    """Error in a RAG factory (component creation)."""


class RAGComponentNotFoundError(RAGFactoryError):
    """The requested component is not registered in the component registry."""
