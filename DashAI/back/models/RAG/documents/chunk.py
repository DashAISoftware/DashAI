from typing import Optional

from DashAI.back.models.RAG.utils import hash_function


class Chunk:
    """A chunk of text extracted from a document.

    Note:
        ``id`` is the ordinal of the chunk inside its chunk set: documents
        sorted by id, then chunks by position. It is set by
        :meth:`ChunkingService.read_chunks`.
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
            The ordinal of the chunk in its chunk set, or None.
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
