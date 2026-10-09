"""PDF text extractor using the pdfminer.six library."""

from typing import ClassVar, Final, List

from DashAI.back.core.schema_fields import (
    BaseSchema,
    bool_field,
    float_field,
    schema_field,
    string_field,
)
from DashAI.back.models.RAG.exceptions import RAGDocumentParsingError
from DashAI.back.models.RAG.extractors.base_extractor import BaseExtractor


class PdfMinerSchema(BaseSchema):
    """Schema for PdfMinerExtractor parameters."""

    password: schema_field(
        string_field(),
        placeholder="",
        description="Password for encrypted PDFs. Leave empty for unencrypted files.",
    )  # type: ignore[valid-type]

    line_margin: schema_field(
        float_field(ge=0.0),
        placeholder=0.5,
        description=(
            "Vertical gap, as a fraction of line height, below which two lines "
            "belong to the same paragraph. Raise it to merge tight line spacing."
        ),
    )  # type: ignore[valid-type]

    char_margin: schema_field(
        float_field(ge=0.0),
        placeholder=2.0,
        description=(
            "Horizontal gap, as a fraction of character width, below which two "
            "characters belong to the same word. Lower it to split joined text."
        ),
    )  # type: ignore[valid-type]

    boxes_flow: schema_field(
        float_field(ge=-1.0, le=1.0),
        placeholder=0.5,
        description=(
            "How much reading order follows horizontal position over vertical "
            "position. -1.0 is strictly left to right, 1.0 strictly top to bottom."
        ),
    )  # type: ignore[valid-type]

    detect_vertical: schema_field(
        bool_field(),
        placeholder=False,
        description="Detect vertically written text, as used in CJK layouts.",
    )  # type: ignore[valid-type]


class PdfMinerExtractor(BaseExtractor):
    """PDF text extractor using the pdfminer.six library.

    Layout analysis is tunable, which matters on multi-column documents where a
    plain content-stream dump interleaves the columns.
    """

    TYPE: Final[str] = "Extractor"
    SCHEMA: ClassVar[BaseSchema] = PdfMinerSchema
    SUPPORTED_FILE_TYPES: List[str] = ["pdf"]

    def __init__(self, **kwargs):
        merged = {
            "password": "",
            "line_margin": 0.5,
            "char_margin": 2.0,
            "boxes_flow": 0.5,
            "detect_vertical": False,
        }
        merged.update(kwargs)
        self.password = merged["password"] or ""
        self.line_margin = merged["line_margin"]
        self.char_margin = merged["char_margin"]
        self.boxes_flow = merged["boxes_flow"]
        self.detect_vertical = merged["detect_vertical"]
        super().__init__(**merged)

    def extract(self, file_path: str) -> str:
        from pdfminer.high_level import extract_text
        from pdfminer.layout import LAParams

        try:
            text = extract_text(
                file_path,
                password=self.password,
                laparams=LAParams(
                    line_margin=self.line_margin,
                    char_margin=self.char_margin,
                    boxes_flow=self.boxes_flow,
                    detect_vertical=self.detect_vertical,
                ),
            )
            return text.strip()
        except Exception as e:
            raise RAGDocumentParsingError(
                f"pdfminer.six failed to extract text from {file_path}: {e}"
            ) from e
