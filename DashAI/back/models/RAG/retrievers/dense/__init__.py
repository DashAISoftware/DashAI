"""Convenience re-exports for all dense retriever types."""

from DashAI.back.models.RAG.retrievers.dense.dense_embedding_retriever import (
    DenseEmbeddingRetriever,
)
from DashAI.back.models.RAG.retrievers.dense.dense_retriever import DenseRetriever

__all__ = ["DenseEmbeddingRetriever", "DenseRetriever"]
