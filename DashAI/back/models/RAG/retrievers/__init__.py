"""Convenience re-exports for all retriever types under a single namespace."""

from DashAI.back.models.RAG.retrievers.base_retriever import BaseRetriever
from DashAI.back.models.RAG.retrievers.composite import (
    CompositeRetriever,
    MMRRerankerRetriever,
    ParallelRetriever,
    SequentialRetriever,
)
from DashAI.back.models.RAG.retrievers.cross_encoder import (
    CrossEncoderRetriever,
    SentenceTransformerCrossEncoderRetriever,
)
from DashAI.back.models.RAG.retrievers.dense import DenseEmbeddingRetriever
from DashAI.back.models.RAG.retrievers.enums import MergeStrategy
from DashAI.back.models.RAG.retrievers.exceptions import (
    CompositeValidationError,
    MissingParameterError,
    RetrieverError,
)
from DashAI.back.models.RAG.retrievers.retriever_factory import (
    RetrieverFactory,
    RetrieverFactoryResult,
)
from DashAI.back.models.RAG.retrievers.sparse import (
    BM25Retriever,
    SparseRetriever,
    TFIDFRetriever,
)
from DashAI.back.models.RAG.retrievers.unit_retriever import UnitRetriever

__all__ = [
    "BM25Retriever",
    "CompositeRetriever",
    "CompositeValidationError",
    "CrossEncoderRetriever",
    "DenseEmbeddingRetriever",
    "MergeStrategy",
    "MissingParameterError",
    "MMRRerankerRetriever",
    "ParallelRetriever",
    "RetrieverError",
    "RetrieverFactory",
    "RetrieverFactoryResult",
    "BaseRetriever",
    "SentenceTransformerCrossEncoderRetriever",
    "SequentialRetriever",
    "SparseRetriever",
    "TFIDFRetriever",
    "UnitRetriever",
]
