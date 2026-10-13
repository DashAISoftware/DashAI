"""Run converters and explorers on the items of a DashAIDocument.

An item is one element of a document: a Text or an Image value plus its
element kind. A tool selects the items it runs on by content type and,
optionally, by kind, so a converter can rewrite only the paragraphs of a
document and an explorer can look only at its headings.

The selected items of one content type reach the tool as a one column
dataset named after the type, so the DashAI type restrictions every
component already declares apply to documents unchanged: a Text tool sees a
``Text`` column and an image tool an ``Image`` column.
"""

import json
import os
from typing import Any, Callable, Dict, List, NamedTuple, Optional, Tuple, Union

import pyarrow as pa

from DashAI.back.dataloaders.classes.dashai_dataset import (
    DashAIDataset,
    get_arrow_table,
)
from DashAI.back.dataloaders.classes.dashai_document import (
    ATTRS_COLUMN,
    CONTENT_COLUMN,
    KIND_COLUMN,
    PAGE_COLUMN,
    POSITION_COLUMN,
    DashAIDocument,
    _content_dashai_type,
    read_content_columns,
)
from DashAI.back.dataloaders.classes.document_elements import TABLE_KIND, table_text
from DashAI.back.types.dashai_image import DashAIImage
from DashAI.back.types.utils import save_types_in_arrow_metadata
from DashAI.back.types.value_types import Text


class ItemFilter(NamedTuple):
    """Which items of one content type a tool runs on.

    Parameters
    ----------
    kinds : List[str], optional
        Element kinds to keep; every kind when None.
    positions : List[int], optional
        Reading order positions of the exact items to keep; every item of
        the kept kinds when None.
    """

    kinds: Optional[List[str]] = None
    positions: Optional[List[int]] = None


ItemSelection = Dict[str, ItemFilter]


def _merge(current: Optional[list], extra: Optional[list]) -> Optional[list]:
    """Union two optional lists, where None means everything."""
    if current is None or extra is None:
        return None
    return list(dict.fromkeys(current + extra))


def resolve_content_type(type_name: str) -> type:
    """Find a supported document content type by its display name.

    Parameters
    ----------
    type_name : str
        ``"Text"`` or ``"Image"``.

    Returns
    -------
    type
        The DashAI type class stored in documents.

    Raises
    ------
    ValueError
        If no supported content type has that name.
    """
    for content_type in DashAIDocument.SUPPORTED_TYPES:
        if content_type.display_name() == type_name:
            return content_type
    raise ValueError(f"Documents have no {type_name} content.")


def selection_from_columns(columns: List[Dict[str, Any]]) -> ItemSelection:
    """Read the items a tool selected from its stored scope columns.

    Each column names a content type in ``columnName``, may list element
    kinds in ``kinds`` and exact item positions in ``positions``. A missing
    or empty list means no restriction on that dimension.

    Parameters
    ----------
    columns : List[Dict[str, Any]]
        The tool's scope columns.

    Returns
    -------
    ItemSelection
        Content type name to its :class:`ItemFilter`, in the order the types
        were first selected.
    """
    selection: ItemSelection = {}
    for column in columns:
        type_name = column.get("columnName")
        kinds = list(dict.fromkeys(column.get("kinds") or [])) or None
        positions = list(dict.fromkeys(column.get("positions") or [])) or None
        if type_name in selection:
            current = selection[type_name]
            selection[type_name] = ItemFilter(
                _merge(current.kinds, kinds), _merge(current.positions, positions)
            )
        else:
            selection[type_name] = ItemFilter(kinds, positions)
    return selection


def check_selection(
    selection: ItemSelection,
    columns_spec: Dict[str, Dict[str, Any]],
    document_path: Optional[Union[str, os.PathLike]] = None,
) -> None:
    """Check that a selection names items the document has.

    Parameters
    ----------
    selection : ItemSelection
        Content type name to its :class:`ItemFilter`.
    columns_spec : Dict[str, Dict[str, Any]]
        The document columns spec from :func:`get_document_columns_spec`.
    document_path : str or os.PathLike, optional
        The saved document, needed to check selected item positions.

    Raises
    ------
    ValueError
        If nothing is selected, a content type or kind has no items, or a
        selected position is not an item of that type and kinds.
    """
    if not selection:
        raise ValueError("Select at least one content type of the document.")
    for type_name, item_filter in selection.items():
        if type_name not in columns_spec:
            raise ValueError(f"The document has no {type_name} items.")
        present = columns_spec[type_name].get("kinds") or {}
        missing = [kind for kind in item_filter.kinds or [] if kind not in present]
        if missing:
            raise ValueError(
                f"The document has no {type_name} items of the kinds "
                f"{', '.join(missing)}."
            )
        if item_filter.positions is None or document_path is None:
            continue
        columns = read_content_columns(
            document_path, resolve_content_type(type_name), with_content=False
        )
        kind_at = dict(zip(columns[POSITION_COLUMN], columns[KIND_COLUMN], strict=True))
        wrong = [
            position
            for position in item_filter.positions
            if position not in kind_at
            or (
                item_filter.kinds is not None
                and kind_at[position] not in item_filter.kinds
            )
        ]
        if wrong:
            raise ValueError(
                f"The items at positions {', '.join(map(str, wrong))} are not "
                f"selected {type_name} items of the document."
            )


def _arrow_table(dataset: DashAIDataset) -> pa.Table:
    """Return the Arrow table of a dataset, honouring any row selection."""
    if isinstance(dataset, DashAIDataset) and dataset._indices is None:
        return get_arrow_table(dataset)
    return dataset.with_format("arrow")[:]


def _selected_indexes(table: pa.Table, item_filter: ItemFilter) -> List[int]:
    """Return the row indexes of a content table the filter keeps."""
    item_kinds = table.column(KIND_COLUMN).to_pylist()
    item_positions = table.column(POSITION_COLUMN).to_pylist()
    kinds = None if item_filter.kinds is None else set(item_filter.kinds)
    positions = None if item_filter.positions is None else set(item_filter.positions)
    return [
        index
        for index, (kind, position) in enumerate(
            zip(item_kinds, item_positions, strict=True)
        )
        if (kinds is None or kind in kinds)
        and (positions is None or position in positions)
    ]


def _matching_indexes(
    table: pa.Table, type_name: str, item_filter: ItemFilter
) -> List[int]:
    """Return the row indexes the filter keeps, refusing an empty match.

    Raises
    ------
    ValueError
        If no item of the content table matches the filter.
    """
    indexes = _selected_indexes(table, item_filter)
    if not indexes:
        raise ValueError(
            f"The document has no {type_name} items matching the kinds "
            f"{item_filter.kinds} and positions {item_filter.positions}."
        )
    return indexes


def _content_table(document: DashAIDocument, type_name: str) -> pa.Table:
    """Return the stored table of one content type of a document.

    Raises
    ------
    ValueError
        If the document has no items of that type.
    """
    content_type = resolve_content_type(type_name)
    table = document.tables.get(content_type)
    if table is None or table.num_rows == 0:
        raise ValueError(f"The document has no {type_name} items.")
    return table


def _column_dataset(
    content_type: type, values: pa.Array, column_name: str
) -> DashAIDataset:
    """Wrap content values in a one column dataset typed as the content."""
    column_type = _content_dashai_type(content_type)
    table = pa.table({column_name: values})
    table = save_types_in_arrow_metadata(table, {column_name: column_type.to_string()})
    return DashAIDataset(table, types={column_name: column_type})


def items_as_column(
    document: DashAIDocument,
    type_name: str,
    item_filter: Optional[ItemFilter] = None,
) -> DashAIDataset:
    """Expose the selected items of one content type as a one column dataset.

    Parameters
    ----------
    document : DashAIDocument
        The document to read.
    type_name : str
        The content type display name, which also names the column.
    item_filter : ItemFilter, optional
        Kinds and positions to keep, by default every item of the type.

    Returns
    -------
    DashAIDataset
        The selected items in reading order, in a column named ``type_name``.

    Raises
    ------
    ValueError
        If the document has no items of that type, or none match the filter.
    """
    item_filter = item_filter or ItemFilter()
    table = _content_table(document, type_name)
    indexes = _matching_indexes(table, type_name, item_filter)
    values = table.column(CONTENT_COLUMN).take(pa.array(indexes, type=pa.int64()))
    return _column_dataset(resolve_content_type(type_name), values, type_name)


def _converted_values(
    converter_name: str,
    type_name: str,
    content_type: type,
    source: DashAIDataset,
    transformed: DashAIDataset,
) -> List[Any]:
    """Check a converter result and return it as storable content values.

    A Text item stays Text: a scalar result, such as a column the converter
    promoted to Integer because every value became a number, is stored back
    as its text. An Image item only accepts images.

    Parameters
    ----------
    converter_name : str
        Converter class name, for the error messages.
    type_name : str
        The converted content type display name.
    content_type : type
        The converted content type class.
    source : DashAIDataset
        The dataset the converter received.
    transformed : DashAIDataset
        The dataset the converter returned.

    Returns
    -------
    List[Any]
        One content value per converted item, in order.

    Raises
    ------
    ValueError
        If the result has more than one column, a different number of rows,
        or values a document cannot store as ``type_name``.
    """
    if len(transformed.column_names) != 1:
        raise ValueError(
            f"{converter_name} produced the columns {transformed.column_names}, "
            f"but a document keeps exactly one value per {type_name} item, so "
            "this converter cannot run on documents."
        )
    if len(transformed) != len(source):
        raise ValueError(
            f"{converter_name} returned {len(transformed)} values for "
            f"{len(source)} {type_name} items; converters that add or remove "
            "items cannot run on documents."
        )
    column = _arrow_table(transformed).column(0)
    output_type = transformed.types.get(transformed.column_names[0])
    produced = (
        output_type.display_name() if output_type is not None else str(column.type)
    )
    if content_type is DashAIImage:
        if produced != DashAIImage.display_name():
            raise ValueError(
                f"{converter_name} turned Image items into {produced}; a "
                "document can only store Image items as images."
            )
        return column.to_pylist()
    if produced == DashAIImage.display_name() or pa.types.is_struct(column.type):
        raise ValueError(
            f"{converter_name} turned Text items into {produced}; a document "
            "can only store Text items as text."
        )
    try:
        values = column.cast(pa.string()).to_pylist()
    except (pa.ArrowInvalid, pa.ArrowNotImplementedError) as e:
        raise ValueError(
            f"{converter_name} returned {produced} values that cannot be stored "
            "as Text."
        ) from e
    if any(value is None for value in values):
        raise ValueError(
            f"{converter_name} left some Text items empty; document items "
            "cannot be missing."
        )
    return values


def _cell_slots(
    kinds: List[str], attrs: List[Dict[str, Any]], indexes: List[int]
) -> List[Optional[List[Tuple[int, int]]]]:
    """Find the cells a converter rewrites in each selected item.

    Parameters
    ----------
    kinds : List[str]
        Element kind of every item of the content table.
    attrs : List[Dict[str, Any]]
        Element attributes of every item of the content table.
    indexes : List[int]
        Row indexes of the selected items.

    Returns
    -------
    List[Optional[List[Tuple[int, int]]]]
        For each selected item, the ``(row, column)`` of its non empty cells
        when it is a table, or None when the item is converted whole.
    """
    slots: List[Optional[List[Tuple[int, int]]]] = []
    for index in indexes:
        if kinds[index] != TABLE_KIND:
            slots.append(None)
            continue
        slots.append(
            [
                (row_index, column_index)
                for row_index, row in enumerate(attrs[index]["rows"])
                for column_index, cell in enumerate(row)
                if cell
            ]
        )
    return slots


def apply_converter_to_document(
    document: DashAIDocument,
    make_converter: Callable[[], Any],
    selection: ItemSelection,
) -> DashAIDocument:
    """Apply a converter to the selected items of a document.

    Each content type is converted on its own with a fresh converter, fitted
    and applied on the selected items only. Every other item, including
    items of the same type with other kinds, keeps its content.

    A table item is converted cell by cell: its ``rows`` attribute is what
    the document shows, so the converter rewrites the cells and the text
    content is rebuilt from them.

    Parameters
    ----------
    document : DashAIDocument
        The document to convert.
    make_converter : Callable[[], Any]
        Returns a new, configured converter instance.
    selection : ItemSelection
        Content type name to the :class:`ItemFilter` of the items to convert.

    Returns
    -------
    DashAIDocument
        The converted document; ``document`` is left unchanged.

    Raises
    ------
    ValueError
        If nothing is selected, a selected type or kind has no items, the
        converter changes the row count, or its result cannot be stored.
    """
    if not selection:
        raise ValueError("Select at least one content type to convert.")
    for type_name, item_filter in selection.items():
        content_type = resolve_content_type(type_name)
        table = _content_table(document, type_name)
        indexes = _matching_indexes(table, type_name, item_filter)
        contents = table.column(CONTENT_COLUMN).to_pylist()
        attrs = [json.loads(value) for value in table.column(ATTRS_COLUMN).to_pylist()]
        slots = _cell_slots(table.column(KIND_COLUMN).to_pylist(), attrs, indexes)
        inputs = []
        for index, cells in zip(indexes, slots, strict=True):
            if cells is None:
                inputs.append(contents[index])
            else:
                rows = attrs[index]["rows"]
                inputs.extend(rows[row][column] for row, column in cells)
        if not inputs:
            continue
        source = _column_dataset(
            content_type,
            pa.array(inputs, type=table.schema.field(CONTENT_COLUMN).type),
            type_name,
        )
        converter = make_converter()
        converter_name = type(converter).__name__
        if getattr(type(converter), "CHANGES_ROW_COUNT", False):
            raise ValueError(
                f"{converter_name} changes the number of rows, which a document "
                "cannot do."
            )
        converter.fit(source, None)
        transformed = converter.transform(source, None)
        values = _converted_values(
            converter_name, type_name, content_type, source, transformed
        )
        outputs = iter(values)
        for index, cells in zip(indexes, slots, strict=True):
            if cells is None:
                contents[index] = next(outputs)
                continue
            rows = [list(row) for row in attrs[index]["rows"]]
            for row, column in cells:
                rows[row][column] = next(outputs)
            attrs[index] = {**attrs[index], "rows": rows}
            contents[index] = table_text(rows)
        replacement = pa.table(
            {
                CONTENT_COLUMN: pa.array(
                    contents, type=table.schema.field(CONTENT_COLUMN).type
                ),
                POSITION_COLUMN: table.column(POSITION_COLUMN),
                PAGE_COLUMN: table.column(PAGE_COLUMN),
                ATTRS_COLUMN: pa.array(
                    [
                        json.dumps(value, sort_keys=True, ensure_ascii=False)
                        for value in attrs
                    ],
                    type=pa.string(),
                ),
            }
        )
        document = document.with_content(content_type, DashAIDataset(replacement))
    return document


def get_document_columns_spec(
    document_path: Union[str, os.PathLike],
) -> Dict[str, Dict[str, Any]]:
    """Describe a saved document as one column per content type.

    Tools check their type restrictions against columns, so each content
    type is one column named after the type. The element kinds of its items
    are listed too, so a tool can be pointed at some of them. No content is
    read: image bytes never leave the file.

    Parameters
    ----------
    document_path : Union[str, os.PathLike]
        The saved document directory.

    Returns
    -------
    Dict[str, Dict[str, Any]]
        Type name to ``{"type", "dtype", "count", "kinds"}``, where ``kinds``
        maps each element kind to its number of items in reading order of
        first appearance. Types without items are left out.

    Raises
    ------
    FileNotFoundError
        If the directory holds no saved document.
    """
    from DashAI.back.dataloaders.classes.dashai_document import (
        DOCUMENT_METADATA_FILE,
    )

    if not os.path.exists(os.path.join(document_path, DOCUMENT_METADATA_FILE)):
        raise FileNotFoundError(f"No saved document in {document_path}.")
    spec: Dict[str, Dict[str, Any]] = {}
    for content_type in (Text, DashAIImage):
        columns = read_content_columns(document_path, content_type, with_content=False)
        if not columns[POSITION_COLUMN]:
            continue
        order = sorted(
            range(len(columns[POSITION_COLUMN])),
            key=lambda index: columns[POSITION_COLUMN][index],
        )
        kinds: Dict[str, int] = {}
        for index in order:
            kind = columns[KIND_COLUMN][index]
            kinds[kind] = kinds.get(kind, 0) + 1
        type_info = _content_dashai_type(content_type).to_string()
        spec[content_type.display_name()] = {
            "type": type_info.get("type"),
            "dtype": type_info.get("dtype"),
            "count": len(order),
            "kinds": kinds,
        }
    return spec
