from typing import Optional

from DashAI.back.models.RAG.utils import hash_function


class Chunk:
    """A chunk of text extracted from a document.

    Note:
        ``id`` starts as ``None`` when the chunk is first created in memory
        (see :meth:`BaseChunkingModel.chunk_document`). It is later set to the
        real database primary key by :meth:`ChunkingService._update_chunk_ids`
        after the chunk is persisted.
    """

    def __init__(
        self,
        id: Optional[int],
        document_id: int,
        document_position: int,
        text: str,
    ):
        """Initialize a Chunk instance.

        Args:
            id: The database primary key, or None if not yet persisted.
            document_id: The ID of the parent document.
            document_position: The 0-based position of this chunk within
                the document.
            text: The text content of the chunk.
        """
        self.id: Optional[int] = id
        self.document_id = document_id
        self.document_position = document_position
        self.text = text
        self.hash = hash_function(text)
