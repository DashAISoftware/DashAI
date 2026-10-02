"""DashAI Document implementation."""

from dataclasses import dataclass
from typing import Any, ClassVar, Dict, List, Optional, Tuple, Type, Union

import pyarrow as pa

from DashAI.back.dataloaders.classes.dashai_data import DashAIData
from DashAI.back.types.dashai_data_type import DashAIDataType
from DashAI.back.types.dashai_image import DashAIImage
from DashAI.back.types.utils import save_types_in_arrow_metadata
from DashAI.back.types.value_types import Integer, Text

CONTENT_COLUMN = "content"
POSITION_COLUMN = "position"
PAGE_COLUMN = "page"
REQUIRED_COLUMNS = (CONTENT_COLUMN, POSITION_COLUMN, PAGE_COLUMN)


@dataclass
class DocumentItem:
    """One piece of content of a document.

    Parameters
    ----------
    type : Type[DashAIDataType]
        DashAI type of the content, ``Text`` or ``DashAIImage``.
    content : str or DashAIImage
        The content itself.
    page : int, optional
        1-based page the content comes from, ``None`` when the source
        format has no pages.
    position : int, optional
        Index of the item in the document's reading order. Assigned by
        ``DashAIDocument``; ignored on input.
    """

    type: Type[DashAIDataType]
    content: Union[str, DashAIImage]
    page: Optional[int] = None
    position: Optional[int] = None


def content_file_stem(content_type: Type[DashAIDataType]) -> str:
    """Return the file stem used to store a content type on disk.

    Parameters
    ----------
    content_type : Type[DashAIDataType]
        A supported content type.

    Returns
    -------
    str
        ``"text"`` for ``Text`` and ``"image"`` for ``DashAIImage``.
    """
    return content_type.display_name().lower()


def _content_arrow_type(content_type: Type[DashAIDataType]) -> pa.DataType:
    """Return the Arrow type of the ``content`` column for a content type."""
    if content_type is Text:
        return pa.string()
    return DashAIImage.pa_type


def _content_dashai_type(content_type: Type[DashAIDataType]) -> DashAIDataType:
    """Return the DashAI type instance describing the ``content`` column."""
    if content_type is Text:
        return Text(pa.string())
    return DashAIImage()


def build_content_table(
    content_type: Type[DashAIDataType],
    contents: List[Any],
    positions: List[int],
    pages: List[Optional[int]],
) -> pa.Table:
    """Build the Arrow table that stores one content type of a document.

    Parameters
    ----------
    content_type : Type[DashAIDataType]
        ``Text`` or ``DashAIImage``.
    contents : list
        Strings for ``Text``; ``{"bytes": ..., "path": ...}`` dicts for images.
    positions : list of int
        Reading-order index of each item.
    pages : list of int or None
        1-based page of each item.

    Returns
    -------
    pa.Table
        Table with ``content``, ``position`` and ``page`` columns and the
        DashAI types stored in the schema metadata.
    """
    schema = pa.schema(
        [
            pa.field(CONTENT_COLUMN, _content_arrow_type(content_type)),
            pa.field(POSITION_COLUMN, pa.int64(), nullable=False),
            pa.field(PAGE_COLUMN, pa.int64()),
        ]
    )
    table = pa.table(
        {
            CONTENT_COLUMN: contents,
            POSITION_COLUMN: positions,
            PAGE_COLUMN: pages,
        },
        schema=schema,
    )
    types = {
        CONTENT_COLUMN: _content_dashai_type(content_type).to_string(),
        POSITION_COLUMN: Integer(pa.int64()).to_string(),
        PAGE_COLUMN: Integer(pa.int64()).to_string(),
    }
    return save_types_in_arrow_metadata(table, types)


class DashAIDocument(DashAIData):
    """A parsed document: content arrays keyed by DashAI type.

    Parameters
    ----------
    contents : Dict[type, pa.Table]
        One table per content type, as built by ``build_content_table``.
    metadata : dict, optional
        Free-form document metadata (file name, file type, page count,
        dataloader and its parameters).

    Raises
    ------
    TypeError
        If a key is not a supported content type.
    ValueError
        If a table misses a required column or two items share a position.
    """

    DATA_KIND: ClassVar[str] = "document"
    SUPPORTED_TYPES: ClassVar[Tuple[type, ...]] = (Text, DashAIImage)

    def __init__(
        self,
        contents: Dict[type, pa.Table],
        metadata: Optional[Dict[str, Any]] = None,
    ):
        seen_positions = set()
        for content_type, table in contents.items():
            self._check_supported(content_type)
            missing = [c for c in REQUIRED_COLUMNS if c not in table.column_names]
            if missing:
                raise ValueError(
                    f"{content_type.display_name()} table is missing columns {missing}."
                )
            positions = table.column(POSITION_COLUMN).to_pylist()
            if seen_positions.intersection(positions) or len(set(positions)) != len(
                positions
            ):
                raise ValueError("Document item positions must be unique.")
            seen_positions.update(positions)
        self._contents = dict(contents)
        self.metadata: Dict[str, Any] = dict(metadata or {})

    @classmethod
    def _check_supported(cls, content_type: Any) -> None:
        """Raise TypeError when ``content_type`` is not supported."""
        if content_type not in cls.SUPPORTED_TYPES:
            supported = ", ".join(t.display_name() for t in cls.SUPPORTED_TYPES)
            raise TypeError(
                f"Unsupported content type {content_type!r}; supported: {supported}."
            )

    @classmethod
    def _encode(cls, item: DocumentItem) -> Any:
        """Validate one item and return its Arrow-ready content value."""
        cls._check_supported(item.type)
        if item.page is not None and (
            not isinstance(item.page, int)
            or isinstance(item.page, bool)
            or item.page < 1
        ):
            raise ValueError(f"Invalid page {item.page!r}: pages start at 1.")
        if item.type is Text:
            if not isinstance(item.content, str):
                raise TypeError("Text content must be str.")
            return item.content
        if not isinstance(item.content, DashAIImage):
            raise TypeError("Image content must be a DashAIImage.")
        if item.content.bytes is None:
            raise ValueError("Image content has no bytes.")
        return {"bytes": item.content.bytes, "path": item.content.path}

    @classmethod
    def from_items(
        cls,
        items: List[DocumentItem],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> "DashAIDocument":
        """Build a document from items listed in reading order.

        Parameters
        ----------
        items : list of DocumentItem
            Items in reading order; their ``position`` is assigned from
            this order.
        metadata : dict, optional
            Document metadata.

        Returns
        -------
        DashAIDocument
            The document with one table per content type present.
        """
        buckets: Dict[type, Dict[str, List[Any]]] = {}
        for position, item in enumerate(items):
            value = cls._encode(item)
            bucket = buckets.setdefault(
                item.type, {"contents": [], "positions": [], "pages": []}
            )
            bucket["contents"].append(value)
            bucket["positions"].append(position)
            bucket["pages"].append(item.page)
        contents = {
            content_type: build_content_table(content_type, **bucket)
            for content_type, bucket in buckets.items()
        }
        return cls(contents, metadata)

    @property
    def tables(self) -> Dict[type, pa.Table]:
        """Return the per-type tables, in ``SUPPORTED_TYPES`` order."""
        return {t: self._contents[t] for t in self.types}

    @property
    def types(self) -> List[type]:
        """Return the content types present, in ``SUPPORTED_TYPES`` order."""
        return [t for t in self.SUPPORTED_TYPES if t in self._contents]

    def count(self, content_type: type) -> int:
        """Return how many items of ``content_type`` the document holds.

        Parameters
        ----------
        content_type : type
            A supported content type.

        Returns
        -------
        int
            Number of items, ``0`` when the type is absent.
        """
        self._check_supported(content_type)
        table = self._contents.get(content_type)
        return 0 if table is None else table.num_rows

    @property
    def content_counts(self) -> Dict[str, int]:
        """Return item counts keyed by the type display name."""
        return {t.display_name(): self.count(t) for t in self.types}

    def __getitem__(self, content_type: type) -> List[Any]:
        """Return the content array of one type.

        Parameters
        ----------
        content_type : type
            ``Text`` or ``DashAIImage``.

        Returns
        -------
        list
            Strings for ``Text``, ``DashAIImage`` instances for images, an
            empty list when the type is absent.
        """
        self._check_supported(content_type)
        table = self._contents.get(content_type)
        if table is None:
            return []
        values = table.column(CONTENT_COLUMN).to_pylist()
        if content_type is Text:
            return values
        return [DashAIImage(bytes=v["bytes"], path=v["path"]) for v in values]

    def items(self) -> List[DocumentItem]:
        """Return every item of the document in reading order.

        Returns
        -------
        list of DocumentItem
            Items with ``position`` and ``page`` filled in.
        """
        result = []
        for content_type in self.types:
            table = self._contents[content_type]
            contents = self[content_type]
            positions = table.column(POSITION_COLUMN).to_pylist()
            pages = table.column(PAGE_COLUMN).to_pylist()
            result.extend(
                DocumentItem(content_type, content, page, position)
                for content, position, page in zip(
                    contents, positions, pages, strict=False
                )
            )
        return sorted(result, key=lambda item: item.position)
