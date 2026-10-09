from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from DashAI.back.models.RAG.documents.file_type import DocumentFileType


class BaseDocument(ABC):
    """Abstract base class for all document types.

    Defines the interface that concrete document classes must implement,
    including text extraction, metadata retrieval, and file type detection.
    """

    SUPPORTED_FILE_TYPES = [
        DocumentFileType.PDF,
        DocumentFileType.TXT,
        # MD, RST, TEX, CSV are handled as TXT via TxtDocument
    ]

    def __init__(
        self,
        id: int,
        file_name: str,
        file_path: str,
        file_hash: str,
        created: Optional[str] = None,
        optional_metadata: Optional[Dict[str, Any]] = None,
        extractor: Optional[Any] = None,
    ):
        """Initialize a BaseDocument instance.

        Args:
            id: The unique identifier of the document.
            file_name: The name of the file.
            file_path: The path to the file.
            file_hash: A hash of the file content.
            created: The creation date of the document.
            optional_metadata: Additional metadata for the document.
            extractor: Optional extractor instance for text extraction.
        """
        self.id = id
        self.file_name = file_name
        self.file_path = file_path
        self.file_hash = file_hash
        self.created = created
        self.optional_metadata = (
            optional_metadata if optional_metadata is not None else {}
        )
        self.extractor = extractor

    @abstractmethod
    def get_text(self) -> str:
        """
        Get the text content of the document.

        Returns:
            str: The text content of the document.
        """

    def _extract_text(self, fallback: callable) -> str:
        """Extract text using the assigned extractor, or fallback callable."""
        if self.extractor is not None:
            return self.extractor.extract(self.file_path)
        return fallback()

    def get_extractor_name(self) -> Optional[str]:
        """Get the extractor component name, or None."""
        if self.extractor is not None:
            return self.extractor.__class__.__name__
        return None

    def get_text_length(self) -> int:
        """
        Get the length of the text content of the document.

        Returns:
            int: The length of the text content of the document.
        """
        return len(self.get_text())

    @abstractmethod
    def get_metadata(self) -> Dict[str, Any]:
        """
        Get the metadata of the document.

        Returns:
            Dict[str, Any]: The metadata of the document.
        """

    def get_id(self) -> int:
        """
        Get the unique identifier of the document.

        Returns:
            int: The unique identifier of the document.
        """
        return self.id

    def get_file_name(self) -> Optional[str]:
        """
        Get the filename of the document.

        Returns:
            Optional[str]: The filename of the document, or None if not applicable.
        """
        return self.file_name

    def get_file_path(self) -> Optional[str]:
        """
        Get the file path of the document.

        Returns:
            Optional[str]: The file path of the document, or None if not applicable.
        """
        return self.file_path

    def get_file_hash(self) -> str:
        """
        Get the hash of the document content.

        Returns:
            str: A hash string representing the document content.
        """
        return self.file_hash

    def get_file_type(self) -> Optional[DocumentFileType]:
        """
        Get the filetype of the document.

        Returns:
            Optional[DocumentFileType]: The filetype of the document,
            or None if not applicable.
        """
        if not self.file_path:
            return None
        ext = self.file_path.split(".")[-1].lower()
        try:
            return DocumentFileType(ext)
        except ValueError:
            return None

    def __repr__(self) -> str:
        """Return a string representation of the BaseDocument.

        Returns:
            str: A string containing the document id, filename, first 50
                characters of text, and metadata.
        """
        return (
            f"BaseDocument(id={self.id}, filename='{self.get_file_name()}', "
            f"content='{self.get_text()[:50]}...', "
            f"metadata={self.get_metadata()})"
        )
