"""Base for converters that rewrite each value of the selected text columns."""

from typing import TYPE_CHECKING, List, Optional, Union

from DashAI.back.converters.base_converter import BaseConverter
from DashAI.back.types.dashai_data_type import DashAIDataType
from DashAI.back.types.value_types import Text

if TYPE_CHECKING:
    from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset


class TextValueConverter(BaseConverter):
    """Rewrite every text value of the selected Text columns, one at a time.

    Subclasses implement :meth:`convert_text`. Missing values stay missing,
    columns that are not Text pass through unchanged, and the rewritten
    columns stay Text. On a document each selected item, or each table
    cell, is one value.
    """

    LEARNS_FROM_DATA = False

    def __init__(self) -> None:
        """Start with no target columns; ``fit`` finds them."""
        super().__init__()
        self._target_columns: List[str] = []

    def convert_text(self, value: str) -> str:
        """Rewrite one text value.

        Parameters
        ----------
        value : str
            The value to rewrite.

        Returns
        -------
        str
            The rewritten value.
        """
        raise NotImplementedError

    def convert_texts(self, values: List[Optional[str]]) -> List[Optional[str]]:
        """Rewrite the values of one column, keeping missing values.

        Parameters
        ----------
        values : List[Optional[str]]
            The column values.

        Returns
        -------
        List[Optional[str]]
            The rewritten values, None where the input was None.
        """
        return [None if value is None else self.convert_text(value) for value in values]

    def get_output_type(self, column_name: Optional[str] = None) -> DashAIDataType:
        """Return Text, the type of every rewritten column.

        Parameters
        ----------
        column_name : str, optional
            Unused; every rewritten column is Text.

        Returns
        -------
        DashAIDataType
            A string backed ``Text`` type.
        """
        import pyarrow as pa

        return Text(arrow_type=pa.string())

    def fit(
        self, x: "DashAIDataset", y: Union["DashAIDataset", None] = None
    ) -> "TextValueConverter":
        """Record which selected columns are Text.

        Parameters
        ----------
        x : DashAIDataset
            The selected columns.
        y : DashAIDataset, optional
            Ignored.

        Returns
        -------
        TextValueConverter
            The fitted converter.
        """
        self._target_columns = [
            name for name in x.column_names if isinstance(x.types.get(name), Text)
        ]
        return self

    def transform(
        self, x: "DashAIDataset", y: Union["DashAIDataset", None] = None
    ) -> "DashAIDataset":
        """Rewrite the values of the fitted Text columns.

        Parameters
        ----------
        x : DashAIDataset
            The dataset to transform.
        y : DashAIDataset, optional
            Ignored.

        Returns
        -------
        DashAIDataset
            The dataset with every Text column rewritten.
        """
        import pyarrow as pa

        from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset

        table = x.arrow_table
        types = dict(x.types)
        for name in self._target_columns:
            if name not in table.column_names:
                continue
            values = self.convert_texts(table.column(name).to_pylist())
            table = table.set_column(
                table.column_names.index(name),
                name,
                pa.array(values, type=pa.string()),
            )
            types[name] = self.get_output_type(name)
        return DashAIDataset(table, types=types)
