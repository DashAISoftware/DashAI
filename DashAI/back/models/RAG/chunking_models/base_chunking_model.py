from abc import ABCMeta, abstractmethod
from bisect import bisect_right
from typing import Final, List

from DashAI.back.config_object import ConfigObject
from DashAI.back.dataloaders.classes.dashai_document import (
    DashAIDocument,
    DocumentItem,
)
from DashAI.back.dataloaders.classes.document_elements import CHUNK_KIND
from DashAI.back.types.value_types import Text

SEPARATOR = "\n\n"


class BaseChunkingModel(ConfigObject, metaclass=ABCMeta):
    """Abstract base class for all chunking models.

    A chunker turns a parsed document into a chunked document with
    :meth:`chunk`. Subclasses only implement :meth:`chunk_text`.
    """

    TYPE: Final[str] = "ChunkingModel"

    CHUNK_UNIT: str = "characters"

    def __init__(self, **kwargs):
        """Validate and store the chunking parameters.

        Parameters
        ----------
        **kwargs
            Parameters matching the subclass schema.
        """
        self.parameters = self.validate_and_transform(kwargs)

    @abstractmethod
    def chunk_text(self, text: str) -> List[str]:
        """Split a text into chunks.

        Parameters
        ----------
        text : str
            The text to split.

        Returns
        -------
        list of str
            The chunks in order.
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
