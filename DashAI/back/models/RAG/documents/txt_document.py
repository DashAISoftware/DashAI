from typing import Any, Dict, Optional

from DashAI.back.models.RAG.documents.base_document import BaseDocument
from DashAI.back.models.RAG.exceptions import RAGDocumentParsingError


class TxtDocument(BaseDocument):
    """Document implementation for plain text (.txt) files.

    Reads text content directly from the file system with UTF-8 encoding.
    """

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
        """Initialize a TxtDocument instance.

        Args:
            id: The unique identifier of the document.
            file_name: The name of the file.
            file_path: The path to the file.
            file_hash: A hash of the file content (computed upstream).
            created: The creation date of the document.
            optional_metadata: Additional metadata for the document.
            extractor: Optional extractor instance for text extraction.
        """
        super().__init__(
            id=id,
            file_name=file_name,
            file_path=file_path,
            file_hash=file_hash,
            created=created,
            optional_metadata=optional_metadata,
            extractor=extractor,
        )

    def get_text(self) -> str:
        return self._extract_text(self._default_extract)

    def _default_extract(self) -> str:
        """Fallback extraction: read as UTF-8 plain text."""
        try:
            with open(self.file_path, "r", encoding="utf-8") as file:
                return file.read().strip()
        except FileNotFoundError as e:
            raise RAGDocumentParsingError(f"File not found: {self.file_path}") from e
        except IOError as e:
            raise RAGDocumentParsingError(
                f"Error reading file {self.file_path}: {str(e)}"
            ) from e
        except UnicodeDecodeError as e:
            raise RAGDocumentParsingError(
                f"Encoding error reading file {self.file_path}: {str(e)}"
            ) from e

    def get_metadata(self) -> Dict[str, Any]:
        base = self.optional_metadata if self.optional_metadata else {}
        base["extractor"] = self.get_extractor_name()
        return base
