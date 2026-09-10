"""PDF text extractor using the PyMuPDF (fitz) library."""

from typing import ClassVar, Final, List

from DashAI.back.core.schema_fields import (
    BaseSchema,
    schema_field,
    string_field,
)
from DashAI.back.models.RAG.exceptions import RAGDocumentParsingError
from DashAI.back.models.RAG.extractors.base_extractor import BaseExtractor


class PyMuPDFSchema(BaseSchema):
    """Schema for PyMuPDFExtractor parameters."""

    password: schema_field(
        string_field(),
        placeholder="",
        description="Password for encrypted PDFs. Leave empty for unencrypted files.",
    )  # type: ignore[valid-type]


class PyMuPDFExtractor(BaseExtractor):
    """PDF text extractor using the PyMuPDF (fitz) library.

    Supports encrypted PDFs via password parameter.
    """

    TYPE: Final[str] = "Extractor"
    SCHEMA: ClassVar[BaseSchema] = PyMuPDFSchema
    SUPPORTED_FILE_TYPES: List[str] = ["pdf"]

    def __init__(self, **kwargs):
        self.password = kwargs.get("password") or None
        super().__init__(**kwargs)

    def extract(self, file_path: str) -> str:
        try:
            import fitz  # pymupdf

            doc = fitz.open(file_path)
            if self.password and doc.needs_pass:
                doc.authenticate(self.password)
            text = ""
            for page in doc:
                text += page.get_text()
            doc.close()
            return text.strip()
        except Exception as e:
            raise RAGDocumentParsingError(
                f"PyMuPDF failed to extract text from {file_path}: {e}"
            ) from e
