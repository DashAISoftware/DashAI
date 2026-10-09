"""Extractor for plain-text file types: txt, md, rst, tex, csv."""

from typing import ClassVar, Final, List

from DashAI.back.core.schema_fields import (
    BaseSchema,
    schema_field,
    string_field,
)
from DashAI.back.models.RAG.exceptions import RAGDocumentParsingError
from DashAI.back.models.RAG.extractors.base_extractor import BaseExtractor


class PlainTextSchema(BaseSchema):
    """Schema for PlainTextExtractor parameters."""

    encoding: schema_field(
        string_field(),
        placeholder="utf-8",
        description="File encoding (e.g. utf-8, latin-1, cp1252)",
    )  # type: ignore


class PlainTextExtractor(BaseExtractor):
    """Extractor for plain-text file types.

    Reads file content with configurable encoding.
    """

    TYPE: Final[str] = "Extractor"
    SCHEMA: ClassVar[BaseSchema] = PlainTextSchema
    SUPPORTED_FILE_TYPES: List[str] = ["txt", "md", "rst", "tex", "csv"]

    def __init__(self, **kwargs):
        self.encoding = kwargs.get("encoding", "utf-8")
        super().__init__(**kwargs)

    def extract(self, file_path: str) -> str:
        try:
            with open(file_path, "r", encoding=self.encoding) as f:
                return f.read().strip()
        except FileNotFoundError as e:
            raise RAGDocumentParsingError(f"File not found: {file_path}") from e
        except (IOError, UnicodeDecodeError, LookupError) as e:
            raise RAGDocumentParsingError(
                f"Error reading {file_path} with encoding '{self.encoding}': {e}"
            ) from e
