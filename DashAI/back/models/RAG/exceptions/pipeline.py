"""Pipeline orchestration RAG exceptions.

These were historically defined inside RAG_pipeline.py and are moved
here so the whole hierarchy lives in one package.
"""

from DashAI.back.models.RAG.exceptions.base import RAGWorkflowError


class RAGPipelineError(RAGWorkflowError):
    """Base exception for RAG pipeline errors."""


class RAGPipelineConfigError(RAGPipelineError):
    """Invalid or missing parameters in pipeline configuration."""


class RAGPipelineInitializationError(RAGPipelineError):
    """Error during RAG pipeline initialization."""


class RAGPipelineRuntimeError(RAGPipelineError):
    """Error during RAG pipeline execution."""


class RAGDatabaseError(RAGPipelineError):
    """Database-related error in RAG pipeline."""


class RAGPipelineInputError(RAGPipelineError):
    """Invalid or malformed input data to the RAG pipeline."""
