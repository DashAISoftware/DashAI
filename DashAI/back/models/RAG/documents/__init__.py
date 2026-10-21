"""Document representation layer for the RAG module.

Provides the source documents a pipeline chunks (``SourceDocument``) and the
``Chunk`` data class retrievers return.
"""

from .chunk import Chunk
from .source_document import SourceDocument

__all__ = ["Chunk", "SourceDocument"]
