"""Document file type enumeration.

Single source of truth for file-type strings used across all
layers (models, services, API).  Each member's value is the
canonical extension string (without the leading dot).
"""

from __future__ import annotations

from enum import Enum


class DocumentFileType(str, Enum):
    """Supported document file extensions.

    Usage::

        from DashAI.back.models.RAG.documents.file_type import DocumentFileType

        # As a string (via ``str`` mixin):
        ft: str = DocumentFileType.PDF  # "pdf"

        # As dict key:
        classes: dict[DocumentFileType, type] = {
            DocumentFileType.PDF: PDFDocument,
        }
    """

    TXT = "txt"
    PDF = "pdf"
    MD = "md"
    RST = "rst"
    TEX = "tex"
    CSV = "csv"

    @classmethod
    def supported_extensions(cls) -> list[str]:
        """Return every supported extension, sorted, without leading dots.

        Used to tell the user which formats *are* accepted when a rejected
        upload would otherwise leave them guessing.
        """
        return sorted(member.value for member in cls)
