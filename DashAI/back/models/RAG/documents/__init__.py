"""Document representation layer for the RAG module.

Provides abstract and concrete document types (BaseDocument, PDFDocument,
TxtDocument), a Chunk data class, and a DocumentFileType enumeration.
"""

from .base_document import BaseDocument
from .chunk import Chunk
from .file_type import DocumentFileType
from .pdf_document import PDFDocument
from .rag_document import RAGDocument, TextSegment
from .txt_document import TxtDocument
