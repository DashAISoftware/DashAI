"""Base for converters that turn each document item into zero or more items."""

from typing import TYPE_CHECKING, Any, Dict, List, Optional

from DashAI.back.converters.base_converter import BaseConverter
from DashAI.back.core.data_kinds import DOCUMENT
from DashAI.back.types.dashai_data_type import DashAIDataType
from DashAI.back.types.value_types import Text

if TYPE_CHECKING:
    from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset

SOURCE_COLUMN = "source"


class DocumentConverter(BaseConverter):
    """A converter that adds, splits or drops document items.

    A dataset converter maps each row to one row, so it cannot say where a
    new value belongs in a document. A document converter receives the
    selected items of one content type as a one column dataset, like every
    converter, and returns a dataset that names the source of each output:

    * ``content``: the new item contents, typed as a document content type
      (``Text`` or ``Image``), which may differ from the input type.
    * ``source``: for each output row, the index of the input row it comes
      from. An input row no output names is dropped from the document.
    * ``kind`` (optional): the element kind of each new item. When missing
      or null, an item of the same type as its source inherits the source
      kind and attributes, and any other item gets the default kind of its
      type. A table is inherited only by an item with the same content, so
      a kept table keeps its rows and a piece of a table is a paragraph.
    * ``attrs`` (optional): the element attributes of each new item, as JSON
      objects, used with ``kind``.

    New items inherit the page of their source and follow it in reading
    order. When ``keep_source`` is True the source items stay and the new
    items are inserted after them; otherwise the new items replace them.
    """

    CHANGES_ROW_COUNT = True
    COLUMN_OPERATION = "rows"
    LEARNS_FROM_DATA = False
    metadata: Dict[str, Any] = {"data_kinds": [DOCUMENT]}
    keep_source: bool = False

    def __init_subclass__(cls, **kwargs: Any) -> None:
        """Limit every subclass to documents, whatever metadata it declares.

        Datasets have no items to split or drop, so ``data_kinds`` is always
        documents only.
        """
        super().__init_subclass__(**kwargs)
        cls.metadata = {**(cls.metadata or {}), "data_kinds": [DOCUMENT]}

    def fit(
        self, x: "DashAIDataset", y: Optional["DashAIDataset"] = None
    ) -> "DocumentConverter":
        """Return the converter unchanged; override to learn from the items.

        Parameters
        ----------
        x : DashAIDataset
            The selected items.
        y : DashAIDataset, optional
            Ignored.

        Returns
        -------
        DocumentConverter
            This converter.
        """
        return self

    def get_output_type(self, column_name: Optional[str] = None) -> DashAIDataType:
        """Return Text, the content type most document converters produce.

        Parameters
        ----------
        column_name : str, optional
            Unused.

        Returns
        -------
        DashAIDataType
            A string backed ``Text`` type.
        """
        import pyarrow as pa

        return Text(arrow_type=pa.string())

    @staticmethod
    def items_result(
        contents: List[Any],
        sources: List[int],
        content_type: type = Text,
        kinds: Optional[List[Optional[str]]] = None,
        attrs: Optional[List[Optional[Dict[str, Any]]]] = None,
    ) -> "DashAIDataset":
        """Build the dataset a document converter returns.

        Parameters
        ----------
        contents : List[Any]
            The new item contents: strings for Text, ``{"bytes", "path"}``
            dicts for images.
        sources : List[int]
            For each new item, the index of the input row it comes from.
        content_type : type, optional
            ``Text`` (default) or ``DashAIImage``.
        kinds : List[Optional[str]], optional
            The element kind of each new item; None inherits or defaults.
        attrs : List[Optional[Dict[str, Any]]], optional
            The element attributes of each new item.

        Returns
        -------
        DashAIDataset
            ``content`` and ``source`` columns, plus ``kind`` and ``attrs``
            when given.
        """
        import json

        import pyarrow as pa

        from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset
        from DashAI.back.types.dashai_image import DashAIImage

        if content_type is DashAIImage:
            content = pa.array(contents, type=DashAIImage.pa_type)
            content_dashai_type = DashAIImage()
        else:
            content = pa.array(contents, type=pa.string())
            content_dashai_type = Text(arrow_type=pa.string())
        columns = {
            "content": content,
            SOURCE_COLUMN: pa.array(sources, type=pa.int64()),
        }
        if kinds is not None:
            columns["kind"] = pa.array(kinds, type=pa.string())
        if attrs is not None:
            columns["attrs"] = pa.array(
                [None if value is None else json.dumps(value) for value in attrs],
                type=pa.string(),
            )
        return DashAIDataset(pa.table(columns), types={"content": content_dashai_type})
