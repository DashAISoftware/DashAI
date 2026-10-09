"""PDF text extractor using the pypdf library."""

from typing import ClassVar, Final, List

from DashAI.back.core.schema_fields import (
    BaseSchema,
    bool_field,
    schema_field,
)
from DashAI.back.models.RAG.exceptions import RAGDocumentParsingError
from DashAI.back.models.RAG.extractors.base_extractor import BaseExtractor


class PypdfSchema(BaseSchema):
    """Schema for PypdfExtractor parameters."""

    strict: schema_field(
        bool_field(),
        placeholder=True,
        description=(
            "If True, raises errors on malformed PDFs. If False, tries to recover."
        ),
    )  # type: ignore[valid-type]


class PypdfExtractor(BaseExtractor):
    """PDF text extractor using the pypdf library."""

    TYPE: Final[str] = "Extractor"
    SCHEMA: ClassVar[BaseSchema] = PypdfSchema
    SUPPORTED_FILE_TYPES: List[str] = ["pdf"]

    def __init__(self, **kwargs):
        self.strict = kwargs.get("strict", True)
        super().__init__(**kwargs)

    def extract(self, file_path: str) -> str:
        from pypdf import PdfReader

        try:
            reader = PdfReader(file_path, strict=self.strict)
            if not reader.pages:
                raise ValueError(f"The PDF file {file_path} is empty or not valid.")
            text = ""
            for page in reader.pages:
                text += page.extract_text() or ""
            return text.strip()
        except Exception as e:
            raise RAGDocumentParsingError(
                f"pypdf failed to extract text from {file_path}: {e}"
            ) from e
