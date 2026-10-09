"""Generation-related RAG exceptions."""

from DashAI.back.models.RAG.exceptions.base import RAGWorkflowError


class RAGGenerationError(RAGWorkflowError):
    """Error during LLM generation."""


class RAGGenerationModelError(RAGGenerationError):
    """The generation model is not a valid TextToTextGenerationTaskModel."""
