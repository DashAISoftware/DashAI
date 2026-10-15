from abc import ABCMeta, abstractmethod
from bisect import bisect_right
from typing import Dict, Final, List

from DashAI.back.config_object import ConfigObject
from DashAI.back.dataloaders.classes.dashai_document import (
    DashAIDocument,
    DocumentItem,
)
from DashAI.back.dataloaders.classes.document_elements import CHUNK_KIND
from DashAI.back.models.RAG.documents.chunk import Chunk
from DashAI.back.models.RAG.documents.rag_document import RAGDocument
from DashAI.back.models.RAG.exceptions import RAGChunkingError
from DashAI.back.types.value_types import Text

SEPARATOR = "\n\n"


class BaseChunkingModel(ConfigObject, metaclass=ABCMeta):
    """Abstract base class for all chunking models.

    Defines the interface and common workflow for chunking strategies.
    Subclasses must implement :meth:`chunk_text`.
    """

    TYPE: Final[str] = "ChunkingModel"
    REQUIRED_EXTRA_KWARGS: Final[List[str]] = ["documents"]

    #: Unit ``chunk_size`` is expressed in: ``"characters"`` or ``"tokens"``.
    #: Lets callers convert a chunk size into a token budget without having to
    #: guess from the class name.
    CHUNK_UNIT: str = "characters"

    def __init__(self, **kwargs):
        """Initialize the chunking model.

        Validates that all required extra keyword arguments are present,
        stores the document mapping, and validates/transforms model parameters.

        Args:
            **kwargs: Must include a ``documents`` key mapping document IDs
                to :class:`RAGDocument` instances. Remaining keys are
                validated and transformed by :meth:`validate_and_transform`.

        Raises:
            RAGChunkingError: If a required extra keyword argument is missing.
        """
        for required_key in self.REQUIRED_EXTRA_KWARGS:
            if required_key not in kwargs:
                raise RAGChunkingError(
                    f"Missing required extra keyword argument: '{required_key}'"
                )
        self.documents: Dict[int, RAGDocument] = kwargs.pop("documents")
        self.parameters = self.validate_and_transform(kwargs)
        self.chunks = None
        self.id = None

    def compute_chunks(self) -> None:
        """Compute chunks if not already done."""
        if self.chunks is None:
            self.chunks = self.chunk_documents()

    @abstractmethod
    def chunk_text(self, text: str, **kwargs) -> List[str]:
        """
        Chunk the input text into smaller pieces.

        Args:
            text (str): The input text to be chunked.
            **kwargs: Additional parameters for chunking.

        Returns:
            List[str]: A list of text chunks.
        """
        raise NotImplementedError("Subclasses must implement the chunk_text method.")

    def chunk(self, document: DashAIDocument) -> DashAIDocument:
        """Split the text items of a document into a chunked document.

        The Text items are joined with ``SEPARATOR`` in reading order and
        passed to :meth:`chunk_text`. Each chunk is located in the joined
        text by searching forward from the previous chunk, and the items it
        overlaps give its pages and sources. Image items are ignored.

        Parameters
        ----------
        document : DashAIDocument
            The parsed source document.

        Returns
        -------
        DashAIDocument
            One Text item of kind ``"chunk"`` per chunk, with ``page`` set to
            the first covered page and ``attrs`` holding ``pages`` (first and
            last page) and ``sources`` (positions of the covered items).
        """
        items = [item for item in document.items() if item.type is Text]
        starts: List[int] = []
        offset = 0
        for item in items:
            starts.append(offset)
            offset += len(item.content) + len(SEPARATOR)
        text = SEPARATOR.join(item.content for item in items)
        chunk_items: List[DocumentItem] = []
        cursor = 0
        for piece in self.chunk_text(text) if text else []:
            found = text.find(piece, cursor) if piece else -1
            start = found if found >= 0 else cursor
            covered = _covered_items(items, starts, start, start + len(piece))
            pages = [item.page for item in covered if item.page is not None]
            chunk_items.append(
                DocumentItem(
                    type=Text,
                    content=piece,
                    page=pages[0] if pages else None,
                    kind=CHUNK_KIND,
                    attrs={
                        "pages": [pages[0], pages[-1]] if pages else [None, None],
                        "sources": [item.position for item in covered],
                    },
                )
            )
            if found >= 0:
                cursor = found + 1
        return DashAIDocument.from_items(
            chunk_items,
            metadata={
                "chunker": type(self).__name__,
                "chunker_params": dict(self.parameters),
            },
        )

    def chunk_document(self, document: RAGDocument) -> Dict[int, Chunk]:
        """Chunk one document and record the page each chunk starts in.

        ``chunk_text`` returns strings, so each chunk is located in the
        document text by searching forward from just after the previous
        chunk's start. A chunk the search cannot find (a chunker that rewrites
        whitespace) inherits the previous position, hence the previous page.

        Parameters
        ----------
        document : RAGDocument
            The document to split.

        Returns
        -------
        Dict[int, Chunk]
            Chunks keyed by their position in the document.

        Raises
        ------
        TypeError
            If ``document`` is not a ``RAGDocument``.
        """
        if not isinstance(document, RAGDocument):
            raise TypeError("Input must be an instance of RAGDocument.")
        text = document.get_text()
        chunks: Dict[int, Chunk] = {}
        cursor = 0
        for idx, chunk_text in enumerate(self.chunk_text(text)):
            found = text.find(chunk_text, cursor) if chunk_text else -1
            start = found if found >= 0 else cursor
            chunks[idx] = Chunk(
                id=None,
                document_id=document.id,
                document_position=idx,
                text=chunk_text,
                page=document.page_at(start),
            )
            if found >= 0:
                cursor = found + 1
        return chunks

    def chunk_documents(self) -> Dict[int, Dict[int, Chunk]]:
        """
        Chunk documents using the chunk_document method.

        Returns:
            Dict[int, Dict[int, Chunk]]: A dictionary mapping document IDs
            to their respective dictionaries of chunk indices and Chunk
            objects.
        """
        chunked_documents = {}
        for document_id, document in self.documents.items():
            chunks = self.chunk_document(document)
            chunked_documents[document_id] = chunks
        return chunked_documents

    def get_chunks(self) -> Dict[int, Dict[int, Chunk]]:
        """
        Get the chunks generated by the chunking model.

        Returns:
            Dict[int, Dict[int, Chunk]]: A dictionary mapping document IDs
            to their respective dictionaries of chunk indices and Chunk
            objects.
        """
        self.compute_chunks()
        return self.chunks

    def get_id(self) -> int:
        """
        Get the ID of the chunking model.

        Returns:
            int: The ID of the chunking model.
        """
        return self.id

    def set_id(self, id: int) -> None:
        """
        Set the ID of the chunking model.

        Args:
            id (int): The ID to set for the chunking model.
        """
        if self.id is None:
            self.id = id
        else:
            raise RAGChunkingError(
                "Chunking model ID is already set and cannot be modified."
            )


def _covered_items(
    items: List[DocumentItem], starts: List[int], start: int, end: int
) -> List[DocumentItem]:
    """Return the items a span of the joined text overlaps.

    Parameters
    ----------
    items : list of DocumentItem
        Text items in reading order.
    starts : list of int
        Offset of each item in the joined text.
    start : int
        First character of the span.
    end : int
        One past the last character of the span.

    Returns
    -------
    list of DocumentItem
        The overlapped items in reading order, at least one when ``items``
        is not empty.
    """
    if not items:
        return []
    first = max(bisect_right(starts, start) - 1, 0)
    if (
        first + 1 < len(items)
        and start >= starts[first] + len(items[first].content)
        and starts[first + 1] < max(end, start + 1)
    ):
        first += 1
    covered = [items[first]]
    index = first + 1
    while index < len(items) and starts[index] < end:
        covered.append(items[index])
        index += 1
    return covered
