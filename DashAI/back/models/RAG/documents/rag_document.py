"""Text of a Data module document, as the RAG chunkers read it."""

from bisect import bisect_right
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from DashAI.back.types.value_types import Text

if TYPE_CHECKING:
    from DashAI.back.dataloaders.classes.dashai_document import DashAIDocument


@dataclass(frozen=True)
class TextSegment:
    """One text item of a document and the page it came from.

    Attributes
    ----------
    text : str
        The item content.
    page : int or None
        1 based page number, or None when the format has no pages.
    """

    text: str
    page: Optional[int] = None


class RAGDocument:
    """Read only text of one ``DataDocument``, with page provenance.

    The text items are joined in reading order with ``SEPARATOR``, so the
    chunkers keep splitting one string, while ``page_at`` maps any offset of
    that string back to the page of the item it falls in.

    Parameters
    ----------
    id : int
        The ``data_document`` primary key.
    name : str
        The document name shown to the user.
    segments : list of TextSegment
        Text items in reading order.
    file_type : str, optional
        Extension of the source file.
    """

    SEPARATOR = "\n\n"

    def __init__(
        self,
        id: int,
        name: str,
        segments: List[TextSegment],
        file_type: Optional[str] = None,
    ) -> None:
        self.id = id
        self.name = name
        self.file_name = name
        self.file_type = file_type
        self.segments = list(segments)
        self._text = self.SEPARATOR.join(segment.text for segment in self.segments)
        self._starts: List[int] = []
        offset = 0
        for segment in self.segments:
            self._starts.append(offset)
            offset += len(segment.text) + len(self.SEPARATOR)

    @classmethod
    def from_dashai_document(
        cls,
        id: int,
        name: str,
        document: "DashAIDocument",
        file_type: Optional[str] = None,
    ) -> "RAGDocument":
        """Build the text view of a parsed document.

        Parameters
        ----------
        id : int
            The ``data_document`` primary key.
        name : str
            The document name shown to the user.
        document : DashAIDocument
            The stored parse. Only its ``Text`` items are kept.
        file_type : str, optional
            Extension of the source file.

        Returns
        -------
        RAGDocument
            One segment per ``Text`` item, in reading order.
        """
        segments = [
            TextSegment(text=item.content, page=item.page)
            for item in document.items()
            if item.type is Text
        ]
        return cls(id=id, name=name, segments=segments, file_type=file_type)

    def get_text(self) -> str:
        """Return the joined text of every segment.

        Returns
        -------
        str
            Segment texts joined with ``SEPARATOR``.
        """
        return self._text

    def page_at(self, offset: int) -> Optional[int]:
        """Return the page of the segment an offset of ``get_text()`` falls in.

        Offsets inside a separator belong to the segment before it.

        Parameters
        ----------
        offset : int
            Character offset into ``get_text()``.

        Returns
        -------
        int or None
            The segment page, or None without segments or pages.
        """
        if not self.segments:
            return None
        index = bisect_right(self._starts, max(offset, 0)) - 1
        return self.segments[max(index, 0)].page

    def get_metadata(self) -> Dict[str, Any]:
        """Return the metadata the prompts and logs show.

        Returns
        -------
        dict
            ``{"name": ..., "file_type": ...}``.
        """
        return {"name": self.name, "file_type": self.file_type}
