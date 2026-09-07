"""Embedding-related RAG exceptions."""

from DashAI.back.models.RAG.exceptions.base import RAGWorkflowError


class RAGEmbeddingError(RAGWorkflowError):
    """Error during embedding computation or loading."""


class RAGEmbeddingLoadError(RAGEmbeddingError):
    """Failed to load embeddings from disk."""


class RAGEmbeddingEmptyInputError(RAGEmbeddingError):
    """Empty input text provided for embedding."""
