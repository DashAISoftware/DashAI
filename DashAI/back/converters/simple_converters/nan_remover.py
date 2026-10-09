from typing import TYPE_CHECKING, List

from DashAI.back.converters.base_converter import BaseConverter
from DashAI.back.converters.category.basic_preprocessing import (
    BasicPreprocessingConverter,
)
from DashAI.back.core.schema_fields.base_schema import BaseSchema
from DashAI.back.core.utils import MultilingualString
from DashAI.back.types.dashai_data_type import DashAIDataType
from DashAI.back.types.missing_values import (  # noqa: F401 (NULL_VALUES re-export)
    NULL_VALUES,
    missing_columns_by_row,
)
from DashAI.back.types.value_types import Text

if TYPE_CHECKING:
    from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset


class NanRemoverSchema(BaseSchema):
    """Schema for NanRemover (no configurable hyperparameters)."""


class NanRemover(BasicPreprocessingConverter, BaseConverter):
    """Remove rows that contain NaN (or null-like) values in the scoped columns.

    Only the columns selected in scope are scanned for nulls; rows with nulls in
    those columns are dropped from the dataset. String representations of null such
    as ``"None"``, ``"nan"``, ``"N/A"`` are also treated as missing.
    """

    SCHEMA = NanRemoverSchema
    CHANGES_ROW_COUNT = True
    COLUMN_OPERATION = "rows"
    ROWS_APPLY_TO = "splits"
    LEARNS_FROM_DATA = False
    DESCRIPTION = MultilingualString(
        en=(
            "Removes the rows with NaN values from the dataset. Keep in mind that "
            "this converter will also remove columns not selected in the scope."
        ),
        es=(
            "Elimina las filas con valores NaN del conjunto de datos. Ten en "
            "cuenta que este convertidor también eliminará las columnas no "
            "seleccionadas en el alcance."
        ),
        pt=(
            "Remove as linhas com valores NaN do conjunto de dados. Tenha em mente "
            "que este conversor também removerá as colunas não selecionadas no escopo."
        ),
        de=(
            "Entfernt Zeilen mit NaN-Werten aus dem Datensatz. Beachten Sie, dass "
            "dieser Konverter auch Spalten entfernt, die nicht im Geltungsbereich "
            "ausgewählt sind."
        ),
        zh=(
            "从数据集中删除含有缺失值（NaN）的行。请注意，此转换器还会删除未在"
            "范围内选择的列。"
        ),
    )
    SHORT_DESCRIPTION = MultilingualString(
        en="Removes the rows with NaN values from the dataset.",
        es="Elimina las filas con valores NaN del conjunto de datos.",
        pt="Remove as linhas com valores NaN do conjunto de dados.",
        de="Entfernt Zeilen mit NaN-Werten aus dem Datensatz.",
        zh="从数据集中删除含有缺失值（NaN）的行。",
    )
    DISPLAY_NAME = MultilingualString(
        en="NaN Remover",
        es="Removedor de NaN",
        pt="Removedor de NaN",
        de="NaN-Entferner",
        zh="缺失值移除器",
    )
    IMAGE_PREVIEW = "nan_remover.png"

    metadata = {
        "allowed_types": [],
        "allowed_dtypes": [],
    }

    def __init__(self):
        """Initialise the NaN remover and set up state.

        The columns and types to process are populated during :meth:`fit`.
        """
        super().__init__()
        self.columns = []
        self.column_types = {}

    def fit(self, x: "DashAIDataset", y: "DashAIDataset" = None) -> "NanRemover":
        """Record the scoped column names and their types for use in ``transform``.

        Parameters
        ----------
        x : DashAIDataset
            The scoped dataset whose column names and types are stored.
        y : DashAIDataset, optional
            Ignored. Defaults to None.

        Returns
        -------
        NanRemover
            The fitted converter instance (self).
        """
        self.columns = x.column_names
        self.column_types = x.types.copy()
        return self

    def transform(
        self, x: "DashAIDataset", y: "DashAIDataset" = None
    ) -> "DashAIDataset":
        """Drop all rows containing null or null-like values in the scoped columns.

        Parameters
        ----------
        x : DashAIDataset
            The dataset to clean.
        y : DashAIDataset, optional
            Ignored. Defaults to None.

        Returns
        -------
        DashAIDataset
            A new dataset with null-containing rows removed.

        Raises
        ------
        ValueError
            If any fitted column is not present in ``x``.
        """
        return x.select_columns(list(self.columns)).select(self.rows_to_keep(x))

    def rows_to_keep(self, x: "DashAIDataset") -> List[int]:
        """Positions of the rows with no missing value in the fitted columns.

        A value is missing following DashAI's shared rule (see
        ``DashAI.back.types.missing_values``): NA, or a null-like string such
        as "N/A" in a text or categorical column.

        Parameters
        ----------
        x : DashAIDataset
            The dataset to inspect; it must contain every fitted column.

        Returns
        -------
        list of int
            0-based positions of the complete rows, in order.

        Raises
        ------
        ValueError
            If any fitted column is not present in ``x``.
        """
        missing_columns = [col for col in self.columns if col not in x.column_names]
        if missing_columns:
            raise ValueError(
                "Cannot remove NaN from columns that do not exist "
                f"in the dataset: {missing_columns}"
            )
        incomplete = missing_columns_by_row(x, list(self.columns))
        return [i for i in range(x.num_rows) if i not in incomplete]

    def get_output_type(self, column_name: str = None) -> DashAIDataType:
        """Return the preserved type for a column, or a Text placeholder.

        Parameters
        ----------
        column_name : str, optional
            Name of the column to look up. Defaults to None.

        Returns
        -------
        DashAIDataType
            The original type stored during ``fit`` if available; otherwise a
            Text type backed by ``pyarrow.string()``.
        """
        import pyarrow as pa

        if column_name and column_name in self.column_types:
            return self.column_types[column_name]
        return Text(arrow_type=pa.string())
