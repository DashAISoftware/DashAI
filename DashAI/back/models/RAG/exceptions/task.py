"""Task-related RAG exceptions."""

from DashAI.back.models.RAG.exceptions.base import RAGWorkflowError


class RAGTaskError(RAGWorkflowError):
    """Error during RAG task execution."""


class RAGTaskInputError(RAGTaskError):
    """Invalid or malformed input to a RAG task."""
