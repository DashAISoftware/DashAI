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
        page: Optional[int] = None,
    ):
        """Initialize a Chunk instance.

        Parameters
        ----------
        id : int or None
            The database primary key, or None if not yet persisted.
        document_id : int
            The ``data_document`` id of the parent document.
        document_position : int
            The 0 based position of this chunk within the document.
        text : str
            The text content of the chunk.
        page : int, optional
            Page of the document item the chunk starts in.
        """
        self.id: Optional[int] = id
        self.document_id = document_id
        self.document_position = document_position
        self.text = text
        self.page = page
        self.hash = hash_function(text)
