"""Document representation layer for the RAG module.

Provides the text view of a Data module document (``RAGDocument``, built from
``TextSegment``s) and the ``Chunk`` data class.
"""

from .chunk import Chunk
from .rag_document import RAGDocument, TextSegment
