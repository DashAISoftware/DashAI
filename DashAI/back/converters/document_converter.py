"""Base for converters that turn each document item into zero or more items."""

from typing import Any, Dict

from DashAI.back.converters.base_converter import BaseConverter
from DashAI.back.core.data_kinds import DOCUMENT

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
      kind and attributes, except a table, and any other item gets the
      default kind of its type.
    * ``attrs`` (optional): the element attributes of each new item, as JSON
      objects, used with ``kind``.

    New items inherit the page of their source and follow it in reading
    order. When ``keep_source`` is True the source items stay and the new
    items are inserted after them; otherwise the new items replace them.
    """

    CHANGES_ROW_COUNT = True
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
