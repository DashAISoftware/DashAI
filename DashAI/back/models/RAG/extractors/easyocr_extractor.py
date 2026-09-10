"""OCR-based PDF text extractor using EasyOCR.

Requires: pip install easyocr
"""

from typing import Final, List

from DashAI.back.core.schema_fields import (
    BaseSchema,
    bool_field,
    list_field,
    schema_field,
)
from DashAI.back.models.RAG.exceptions import RAGDocumentParsingError
from DashAI.back.models.RAG.extractors.base_extractor import BaseExtractor


class EasyOCRSchema(BaseSchema):
    """Schema for EasyOCR extractor parameters."""

    languages: schema_field(
        list_field(str),
        placeholder=["en"],
        description="Language codes for OCR (e.g. ['en'], ['es'], ['en','fr'])",
    )  # type: ignore

    gpu: schema_field(
        bool_field(),
        placeholder=True,
        description="Use GPU acceleration if available",
    )  # type: ignore


class EasyOCRExtractor(BaseExtractor):
    """PDF text extractor using EasyOCR.

    Converts PDF pages to images and runs OCR on each page.
    Works with any language supported by EasyOCR (80+ languages).
    No external system dependencies - pure pip install.
    """

    TYPE: Final[str] = "Extractor"
    SCHEMA: BaseSchema = EasyOCRSchema
    SUPPORTED_FILE_TYPES: List[str] = ["pdf"]

    def __init__(self, **kwargs):
        """Initialize the EasyOCR extractor with the given parameters.

        Args:
            languages (List[str]): Language codes for OCR.
            gpu (bool): Use GPU acceleration if available.
        """
        merged = {"languages": ["en"], "gpu": True}
        merged.update(kwargs)
        self.languages = merged["languages"]
        self.gpu = merged["gpu"]
        super().__init__(**merged)

    def extract(self, file_path: str) -> str:
        """Extract text from PDF using EasyOCR.

        Converts each PDF page to an image and runs OCR.

        Args:
            file_path: Path to the PDF file.

        Returns:
            Extracted text content, pages joined by newlines.

        Raises:
            RAGDocumentParsingError: If extraction fails.
        """
        try:
            import easyocr
            import fitz  # pymupdf
            import numpy as np
        except ImportError as e:
            raise RAGDocumentParsingError(
                f"EasyOCRExtractor requires pymupdf and easyocr: {e}"
            ) from e

        try:
            reader = easyocr.Reader(self.languages, gpu=self.gpu)
        except Exception as e:
            raise RAGDocumentParsingError(
                f"Failed to initialize EasyOCR reader: {e}"
            ) from e

        try:
            doc = fitz.open(file_path)
            texts = []
            for page in doc:
                # Render page to image
                pix = page.get_pixmap(dpi=200)
                img_array = np.frombuffer(pix.samples, dtype=np.uint8).reshape(
                    pix.height, pix.width, pix.n
                )
                # OCR
                result = reader.readtext(img_array, detail=0)
                page_text = " ".join(result)
                if page_text.strip():
                    texts.append(page_text)
            doc.close()
            return "\n\n".join(texts).strip()
        except Exception as e:
            raise RAGDocumentParsingError(
                f"EasyOCR failed to extract text from {file_path}: {e}"
            ) from e
