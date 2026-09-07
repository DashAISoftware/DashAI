"""Document-related RAG exceptions."""

from DashAI.back.models.RAG.exceptions.base import RAGWorkflowError


class RAGDocumentError(RAGWorkflowError):
    """Error in document loading or processing."""


class RAGDocumentParsingError(RAGDocumentError):
    """Error parsing a document file (e.g. PDF extraction failure)."""


class RAGDocumentNotFoundError(RAGDocumentError):
    """Referenced document does not exist."""


class RAGDocumentFileTypeError(RAGDocumentError):
    """Unsupported or unrecognized document file type."""


class RAGDocumentExtractionError(RAGDocumentError):
    """Error while extracting text from a document (e.g. during upload)."""
