from typing import Any, Dict, Optional

from DashAI.back.models.RAG.documents.base_document import BaseDocument
from DashAI.back.models.RAG.exceptions import RAGDocumentParsingError


class PDFDocument(BaseDocument):
    """Document implementation for PDF files."""

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
        if self.extractor is None:
            raise RAGDocumentParsingError(
                f"No extractor available for PDF file {self.file_path}"
            )
        return self.extractor.extract(self.file_path)

    def get_metadata(self) -> Dict[str, Any]:
        base = self.optional_metadata if self.optional_metadata else {}
        base["extractor"] = self.get_extractor_name()
        return base
