"""Query transformation RAG exceptions."""

from DashAI.back.models.RAG.exceptions.base import RAGWorkflowError


class RAGTransformationError(RAGWorkflowError):
    """Base exception for the optional query transformation stage."""


class RAGTransformationConfigError(RAGTransformationError):
    """Invalid configuration for a query transformer.

    Raised when building a transformer with a bad schema (for example an LLM
    of the wrong type) or when a required parameter such as the prompt or the
    LLM model is missing.
    """


class RAGTransformationOutputError(RAGTransformationError):
    """The model output could not be parsed into the function-call contract.

    The message carries a short, truncated preview of the raw output so the
    failure can be diagnosed without leaking full user text.
    """
