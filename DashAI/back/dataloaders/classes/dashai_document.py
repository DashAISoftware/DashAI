"""DashAI Document implementation."""

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, ClassVar, Dict, List, Optional, Tuple, Type, Union

import pyarrow as pa
import pyarrow.compute as pc

from DashAI.back.core.atomic import atomic_directory
from DashAI.back.dataloaders.classes.dashai_data import DashAIData
from DashAI.back.dataloaders.classes.dashai_dataset import (
    DashAIDataset,
    get_arrow_table,
)
from DashAI.back.dataloaders.classes.document_elements import (
    default_kind,
    validate_element,
)
from DashAI.back.types.dashai_data_type import DashAIDataType
from DashAI.back.types.dashai_image import DashAIImage
from DashAI.back.types.utils import save_types_in_arrow_metadata
from DashAI.back.types.value_types import Integer, Text

CONTENT_COLUMN = "content"
POSITION_COLUMN = "position"
PAGE_COLUMN = "page"
KIND_COLUMN = "kind"
ATTRS_COLUMN = "attrs"
REQUIRED_COLUMNS = (CONTENT_COLUMN, POSITION_COLUMN, PAGE_COLUMN)
STORED_COLUMNS = REQUIRED_COLUMNS + (KIND_COLUMN, ATTRS_COLUMN)


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
    kind : str, optional
        Structural element kind (see ``document_elements.ELEMENT_KINDS``);
        ``None`` means ``"paragraph"`` for Text and ``"image"`` for images.
    attrs : dict, optional
        Attributes of the element kind, such as a heading ``level`` or the
        ``rows`` of a table.
    """

    type: Type[DashAIDataType]
    content: Union[str, DashAIImage]
    page: Optional[int] = None
    position: Optional[int] = None
    kind: Optional[str] = None
    attrs: Optional[Dict[str, Any]] = None


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
    kinds: Optional[List[str]] = None,
    attrs: Optional[List[Dict[str, Any]]] = None,
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
    kinds : list of str, optional
        Element kind of each item; defaults to the kind of the type.
    attrs : list of dict, optional
        Element attributes of each item; defaults to empty dicts.

    Returns
    -------
    pa.Table
        Table with ``content``, ``position``, ``page``, ``kind`` and
        ``attrs`` (JSON) columns and the DashAI types in the schema metadata.
    """
    count = len(contents)
    if kinds is None:
        kinds = [default_kind(content_type)] * count
    if attrs is None:
        attrs = [{}] * count
    schema = pa.schema(
        [
            pa.field(CONTENT_COLUMN, _content_arrow_type(content_type)),
            pa.field(POSITION_COLUMN, pa.int64(), nullable=False),
            pa.field(PAGE_COLUMN, pa.int64()),
            pa.field(KIND_COLUMN, pa.string(), nullable=False),
            pa.field(ATTRS_COLUMN, pa.string(), nullable=False),
        ]
    )
    table = pa.table(
        {
            CONTENT_COLUMN: contents,
            POSITION_COLUMN: positions,
            PAGE_COLUMN: pages,
            KIND_COLUMN: kinds,
            ATTRS_COLUMN: [
                json.dumps(value, sort_keys=True, ensure_ascii=False) for value in attrs
            ],
        },
        schema=schema,
    )
    types = {
        CONTENT_COLUMN: _content_dashai_type(content_type).to_string(),
        POSITION_COLUMN: Integer(pa.int64()).to_string(),
        PAGE_COLUMN: Integer(pa.int64()).to_string(),
        KIND_COLUMN: Text(pa.string()).to_string(),
        ATTRS_COLUMN: Text(pa.string()).to_string(),
    }
    return save_types_in_arrow_metadata(table, types)


def _with_element_columns(content_type: type, table: pa.Table) -> pa.Table:
    """Add default ``kind`` and ``attrs`` columns to a format 1 table.

    Parameters
    ----------
    content_type : type
        ``Text`` or ``DashAIImage``.
    table : pa.Table
        A content table, possibly saved before element kinds existed.

    Returns
    -------
    pa.Table
        The table unchanged when it already has both columns, else rebuilt
        with ``paragraph`` / ``image`` kinds and empty attributes.
    """
    if KIND_COLUMN in table.column_names and ATTRS_COLUMN in table.column_names:
        return table
    return build_content_table(
        content_type,
        table.column(CONTENT_COLUMN).to_pylist(),
        table.column(POSITION_COLUMN).to_pylist(),
        table.column(PAGE_COLUMN).to_pylist(),
    )


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
            self._validate_table(content_type, table)
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

    @staticmethod
    def _validate_table(content_type: type, table: pa.Table) -> None:
        """Check one content table before it becomes part of a document.

        Parameters
        ----------
        content_type : type
            The content type the table is stored under.
        table : pa.Table
            The table to check.

        Raises
        ------
        ValueError
            If a column is missing, the content column has the wrong Arrow
            type, content or positions are null, an image has no bytes, a
            page is lower than 1, or an element kind or its attributes are
            invalid.
        """
        name = content_type.display_name()
        missing = [c for c in STORED_COLUMNS if c not in table.column_names]
        if missing:
            raise ValueError(f"{name} table is missing columns {missing}.")
        expected = _content_arrow_type(content_type)
        if not table.schema.field(CONTENT_COLUMN).type.equals(expected):
            raise ValueError(f"{name} content column must have Arrow type {expected}.")
        content = table.column(CONTENT_COLUMN)
        if content.null_count:
            raise ValueError(f"{name} content cannot be null.")
        if (
            content_type is DashAIImage
            and table.num_rows
            and content.combine_chunks().field("bytes").null_count
        ):
            raise ValueError("Image content has no bytes.")
        if table.column(POSITION_COLUMN).null_count:
            raise ValueError("Document item positions cannot be null.")
        pages = table.column(PAGE_COLUMN)
        if table.num_rows and pages.null_count < len(pages):
            lowest = pc.min(pages).as_py()
            if lowest < 1:
                raise ValueError(f"Invalid page {lowest!r}: pages start at 1.")
        kinds = table.column(KIND_COLUMN)
        attrs = table.column(ATTRS_COLUMN)
        if kinds.null_count or attrs.null_count:
            raise ValueError(f"{name} element kinds and attributes cannot be null.")
        for kind, raw in zip(kinds.to_pylist(), attrs.to_pylist(), strict=True):
            validate_element(kind, content_type, json.loads(raw))

    @classmethod
    def _encode(cls, item: DocumentItem) -> Tuple[Any, str, Dict[str, Any]]:
        """Validate one item and return its content value, kind and attrs."""
        cls._check_supported(item.type)
        kind = item.kind or default_kind(item.type)
        attrs = validate_element(kind, item.type, item.attrs)
        return cls._encode_content(item), kind, attrs

    @classmethod
    def _encode_content(cls, item: DocumentItem) -> Any:
        """Validate one item's page and content and return the Arrow value."""
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
            value, kind, attrs = cls._encode(item)
            bucket = buckets.setdefault(
                item.type,
                {
                    "contents": [],
                    "positions": [],
                    "pages": [],
                    "kinds": [],
                    "attrs": [],
                },
            )
            bucket["contents"].append(value)
            bucket["positions"].append(position)
            bucket["pages"].append(item.page)
            bucket["kinds"].append(kind)
            bucket["attrs"].append(attrs)
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
            Items with ``position``, ``page``, ``kind`` and ``attrs`` filled in.
        """
        result = []
        for content_type in self.types:
            table = self._contents[content_type]
            contents = self[content_type]
            positions = table.column(POSITION_COLUMN).to_pylist()
            pages = table.column(PAGE_COLUMN).to_pylist()
            kinds = table.column(KIND_COLUMN).to_pylist()
            attrs = [json.loads(v) for v in table.column(ATTRS_COLUMN).to_pylist()]
            result.extend(
                DocumentItem(content_type, content, page, position, kind, attr)
                for content, position, page, kind, attr in zip(
                    contents, positions, pages, kinds, attrs, strict=True
                )
            )
        return sorted(result, key=lambda item: item.position)

    def _table_or_empty(self, content_type: type) -> pa.Table:
        """Return the table of a type, or an empty typed table if absent."""
        table = self._contents.get(content_type)
        if table is None:
            return build_content_table(content_type, [], [], [])
        return table

    def as_dataset(self, content_type: type) -> DashAIDataset:
        """Return one content type as a DashAI dataset.

        Parameters
        ----------
        content_type : type
            ``Text`` or ``DashAIImage``.

        Returns
        -------
        DashAIDataset
            Dataset with ``content``, ``position``, ``page``, ``kind`` and
            ``attrs`` columns, empty when the type is absent.
        """
        self._check_supported(content_type)
        return DashAIDataset(self._table_or_empty(content_type))

    def with_content(
        self, content_type: type, dataset: DashAIDataset
    ) -> "DashAIDocument":
        """Return a new document with one content type replaced.

        Parameters
        ----------
        content_type : type
            ``Text`` or ``DashAIImage``.
        dataset : DashAIDataset
            New contents, with ``content``, ``position`` and ``page``
            columns and the same positions as the current contents. Each
            item keeps its current ``kind``, and its current ``attrs``
            unless the dataset has an ``attrs`` column of JSON objects.

        Returns
        -------
        DashAIDocument
            A new document; this one is left unchanged.

        Raises
        ------
        ValueError
            If columns are missing, the positions differ, or the new
            contents are invalid (null content, image without bytes, page
            lower than 1, attributes the item kind does not take).
        """
        self._check_supported(content_type)
        if isinstance(dataset, DashAIDataset) and dataset._indices is None:
            table = get_arrow_table(dataset)
        else:
            table = dataset.with_format("arrow")[:]
        missing = [c for c in REQUIRED_COLUMNS if c not in table.column_names]
        if missing:
            raise ValueError(f"Replacement dataset is missing columns {missing}.")
        current = self._table_or_empty(content_type)
        positions = table.column(POSITION_COLUMN).to_pylist()
        if positions != current.column(POSITION_COLUMN).to_pylist():
            raise ValueError(
                "Replacement must keep the same item positions, in the same order."
            )
        attrs_source = table if ATTRS_COLUMN in table.column_names else current
        rebuilt = build_content_table(
            content_type,
            table.column(CONTENT_COLUMN).to_pylist(),
            positions,
            table.column(PAGE_COLUMN).to_pylist(),
            current.column(KIND_COLUMN).to_pylist(),
            [json.loads(v) for v in attrs_source.column(ATTRS_COLUMN).to_pylist()],
        )
        contents = dict(self._contents)
        if rebuilt.num_rows:
            contents[content_type] = rebuilt
        else:
            contents.pop(content_type, None)
        return DashAIDocument(contents, self.metadata)


DOCUMENT_METADATA_FILE = "document.json"
DOCUMENT_FORMAT_VERSION = 2
READABLE_FORMAT_VERSIONS = (1, 2)


def save_document(document: DashAIDocument, path: Union[str, os.PathLike]) -> None:
    """Save a document to disk.

    Writes one Arrow IPC file per content type present (``text.arrow``,
    ``image.arrow``) and ``document.json`` with the metadata and counts.
    The directory is replaced atomically, so no file from a previous
    version survives.

    Parameters
    ----------
    document : DashAIDocument
        The document to persist.
    path : str or os.PathLike
        Target directory.
    """
    with atomic_directory(Path(path)) as tmp_dir:
        for content_type, table in document.tables.items():
            file_path = tmp_dir / f"{content_file_stem(content_type)}.arrow"
            with pa.OSFile(str(file_path), "wb") as sink:
                writer = pa.ipc.new_file(sink, table.schema)
                writer.write_table(table)
                writer.close()
        sidecar = {
            "version": DOCUMENT_FORMAT_VERSION,
            "metadata": document.metadata,
            "content_counts": document.content_counts,
        }
        with open(tmp_dir / DOCUMENT_METADATA_FILE, "w", encoding="utf-8") as f:
            json.dump(sidecar, f, indent=2, sort_keys=True, ensure_ascii=False)


def load_document(path: Union[str, os.PathLike]) -> DashAIDocument:
    """Load a document saved with :func:`save_document`.

    Parameters
    ----------
    path : str or os.PathLike
        Directory holding ``document.json`` and the per-type Arrow files.

    Returns
    -------
    DashAIDocument
        The restored document.

    Raises
    ------
    FileNotFoundError
        If ``document.json`` or a content file it lists does not exist.
    ValueError
        If the format version is unknown, a listed content type is not
        supported, or a content file holds a different number of items
        than ``document.json`` records.
    """
    directory = Path(path)
    sidecar_path = directory / DOCUMENT_METADATA_FILE
    if not sidecar_path.exists():
        raise FileNotFoundError(f"No {DOCUMENT_METADATA_FILE} in {directory}.")
    with open(sidecar_path, "r", encoding="utf-8") as f:
        sidecar = json.load(f)
    version = sidecar.get("version")
    if version not in READABLE_FORMAT_VERSIONS:
        raise ValueError(
            f"Unsupported document format version {version!r} in {directory}."
        )
    types_by_name = {t.display_name(): t for t in DashAIDocument.SUPPORTED_TYPES}
    contents = {}
    for name, expected in sidecar.get("content_counts", {}).items():
        content_type = types_by_name.get(name)
        if content_type is None:
            raise ValueError(f"Unsupported content type {name!r} in {directory}.")
        file_path = directory / f"{content_file_stem(content_type)}.arrow"
        if not file_path.exists():
            raise FileNotFoundError(f"{file_path.name} is missing from {directory}.")
        with pa.OSFile(str(file_path), "rb") as source:
            table = pa.ipc.open_file(source).read_all()
        if table.num_rows != expected:
            raise ValueError(
                f"{file_path.name} holds {table.num_rows} items, expected {expected}."
            )
        contents[content_type] = _with_element_columns(content_type, table)
    return DashAIDocument(contents, sidecar.get("metadata", {}))


def _content_file(path: Union[str, os.PathLike], content_type: type) -> Path:
    """Return the Arrow file that stores one content type of a saved document."""
    DashAIDocument._check_supported(content_type)
    return Path(path) / f"{content_file_stem(content_type)}.arrow"


def read_content_columns(
    path: Union[str, os.PathLike], content_type: type, with_content: bool = True
) -> Dict[str, List[Any]]:
    """Read one content type of a saved document without loading the others.

    The file is memory mapped and only the requested columns are copied out,
    so asking for positions and pages never copies image bytes.

    Parameters
    ----------
    path : str or os.PathLike
        Directory written by :func:`save_document`.
    content_type : type
        ``Text`` or ``DashAIImage``.
    with_content : bool
        Whether to include the ``content`` column.

    Returns
    -------
    Dict[str, List[Any]]
        Column name to Python values, ``attrs`` parsed into dicts; empty
        lists when the type is absent.
    """
    names = (CONTENT_COLUMN,) if with_content else ()
    names += (POSITION_COLUMN, PAGE_COLUMN)
    file_path = _content_file(path, content_type)
    if not file_path.exists():
        return {name: [] for name in names + (KIND_COLUMN, ATTRS_COLUMN)}
    with pa.memory_map(str(file_path), "r") as source:
        table = pa.ipc.open_file(source).read_all()
        columns = {name: table.column(name).to_pylist() for name in names}
        count = table.num_rows
        has_elements = KIND_COLUMN in table.column_names
        kinds = table.column(KIND_COLUMN).to_pylist() if has_elements else None
        attrs = table.column(ATTRS_COLUMN).to_pylist() if has_elements else None
        del table
    columns[KIND_COLUMN] = kinds or [default_kind(content_type)] * count
    columns[ATTRS_COLUMN] = [json.loads(v) for v in attrs] if attrs else [{}] * count
    return columns


def read_content_at(
    path: Union[str, os.PathLike], content_type: type, position: int
) -> Optional[Any]:
    """Read the content of a single item of a saved document.

    Parameters
    ----------
    path : str or os.PathLike
        Directory written by :func:`save_document`.
    content_type : type
        ``Text`` or ``DashAIImage``.
    position : int
        Reading order position of the item.

    Returns
    -------
    Any or None
        A string for ``Text``, a ``{"bytes", "path"}`` dict for images, or
        None when no item of that type sits at ``position``.
    """
    file_path = _content_file(path, content_type)
    if not file_path.exists():
        return None
    with pa.memory_map(str(file_path), "r") as source:
        table = pa.ipc.open_file(source).read_all()
        positions = table.column(POSITION_COLUMN).to_pylist()
        value = (
            table.column(CONTENT_COLUMN)[positions.index(position)].as_py()
            if position in positions
            else None
        )
        del table
    return value
