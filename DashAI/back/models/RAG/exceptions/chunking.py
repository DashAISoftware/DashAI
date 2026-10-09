"""Chunking-related RAG exceptions."""

from DashAI.back.models.RAG.exceptions.base import RAGWorkflowError


class RAGChunkingError(RAGWorkflowError):
    """Error during document chunking."""


class RAGChunkingOverlapError(RAGChunkingError):
    """chunk_overlap is >= chunk_size, which would cause an infinite loop."""
