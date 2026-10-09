"""Prompt-related RAG exceptions."""

from DashAI.back.models.RAG.exceptions.base import RAGWorkflowError


class RAGPromptError(RAGWorkflowError):
    """Error in prompt template handling."""


class RAGPromptValidationError(RAGPromptError):
    """Prompt template validation failed (missing placeholders, etc.)."""


class RAGPromptTemplateError(RAGPromptError):
    """The prompt template is missing required placeholders or is malformed."""
