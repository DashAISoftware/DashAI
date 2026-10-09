"""PDF text extractor using the pdfplumber library."""

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


class PdfPlumberSchema(BaseSchema):
    """Schema for PdfPlumberExtractor parameters."""

    password: schema_field(
        string_field(),
        placeholder="",
        description="Password for encrypted PDFs. Leave empty for unencrypted files.",
    )  # type: ignore[valid-type]

    x_tolerance: schema_field(
        float_field(gt=0.0),
        placeholder=3.0,
        description=(
            "Horizontal distance, in points, below which two characters belong to "
            "the same word. Lower it when words run together."
        ),
    )  # type: ignore[valid-type]

    y_tolerance: schema_field(
        float_field(gt=0.0),
        placeholder=3.0,
        description=(
            "Vertical distance, in points, below which two characters belong to "
            "the same line. Raise it when a line is split in two."
        ),
    )  # type: ignore[valid-type]

    layout: schema_field(
        bool_field(),
        placeholder=False,
        description=(
            "Pad the output with whitespace so it mirrors the position of the text "
            "on the page. Preserves columns at the cost of extra whitespace."
        ),
    )  # type: ignore[valid-type]

    extract_tables: schema_field(
        bool_field(),
        placeholder=False,
        description=(
            "Append each detected table after the page text, as tab separated "
            "rows. Useful for documents whose data lives in tables."
        ),
    )  # type: ignore[valid-type]


class PdfPlumberExtractor(BaseExtractor):
    """PDF text extractor using the pdfplumber library.

    Builds on pdfminer.six with word and table detection, so it can keep tabular
    content readable instead of flattening it into a run of numbers.
    """

    TYPE: Final[str] = "Extractor"
    SCHEMA: ClassVar[BaseSchema] = PdfPlumberSchema
    SUPPORTED_FILE_TYPES: List[str] = ["pdf"]

    def __init__(self, **kwargs):
        merged = {
            "password": "",
            "x_tolerance": 3.0,
            "y_tolerance": 3.0,
            "layout": False,
            "extract_tables": False,
        }
        merged.update(kwargs)
        self.password = merged["password"] or ""
        self.x_tolerance = merged["x_tolerance"]
        self.y_tolerance = merged["y_tolerance"]
        self.layout = merged["layout"]
        self.extract_tables = merged["extract_tables"]
        super().__init__(**merged)

    @staticmethod
    def _render_table(table: List[List[object]]) -> str:
        """Render one extracted table as tab separated rows.

        Parameters
        ----------
        table : List[List[object]]
            Rows of cells as pdfplumber returns them. Empty cells are ``None``.

        Returns
        -------
        str
            The table as newline separated rows of tab separated cells.
        """
        rows = []
        for row in table:
            rows.append("\t".join(str(cell) if cell else "" for cell in row))
        return "\n".join(rows)

    def extract(self, file_path: str) -> str:
        import pdfplumber

        try:
            parts = []
            with pdfplumber.open(file_path, password=self.password) as pdf:
                for page in pdf.pages:
                    text = page.extract_text(
                        x_tolerance=self.x_tolerance,
                        y_tolerance=self.y_tolerance,
                        layout=self.layout,
                    )
                    if text and text.strip():
                        parts.append(text.strip())
                    if self.extract_tables:
                        for table in page.extract_tables():
                            rendered = self._render_table(table)
                            if rendered.strip():
                                parts.append(rendered)
            return "\n\n".join(parts).strip()
        except Exception as e:
            raise RAGDocumentParsingError(
                f"pdfplumber failed to extract text from {file_path}: {e}"
            ) from e
