"""Retriever-related RAG exceptions."""

from DashAI.back.models.RAG.exceptions.base import RAGWorkflowError


class RAGRetrieverError(RAGWorkflowError):
    """Error during retrieval."""


class RAGRetrieverMissingParameterError(RAGRetrieverError):
    """A required parameter was not provided to the retriever."""


class RAGRetrieverCompositeValidationError(RAGRetrieverError):
    """A composite retriever has an invalid configuration."""


class RAGRetrieverEmptyChildrenError(RAGRetrieverError):
    """A composite retriever was configured with no children."""
