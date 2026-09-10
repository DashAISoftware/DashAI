"""Convenience re-exports for all retriever types under a single namespace."""

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
from DashAI.back.models.RAG.retrievers.dense import (
    DenseEmbeddingRetriever,
    DenseRetriever,
    HuggingFaceDenseRetriever,
)
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
from DashAI.back.models.RAG.retrievers.retriever_model import RetrieverModel
from DashAI.back.models.RAG.retrievers.sparse import (
    BM25Retriever,
    BM25VectorizerModel,
    SparseRetriever,
    TFIDFRetriever,
    TFIDFVectorizerModel,
)
from DashAI.back.models.RAG.retrievers.unit_retriever import UnitRetriever

__all__ = [
    "BM25Retriever",
    "BM25VectorizerModel",
    "CompositeRetriever",
    "CompositeValidationError",
    "CrossEncoderRetriever",
    "DenseEmbeddingRetriever",
    "DenseRetriever",
    "HuggingFaceDenseRetriever",
    "MergeStrategy",
    "MissingParameterError",
    "MMRRerankerRetriever",
    "ParallelRetriever",
    "RetrieverError",
    "RetrieverFactory",
    "RetrieverFactoryResult",
    "RetrieverModel",
    "SentenceTransformerCrossEncoderRetriever",
    "SequentialRetriever",
    "SparseRetriever",
    "TFIDFRetriever",
    "TFIDFVectorizerModel",
    "UnitRetriever",
]
