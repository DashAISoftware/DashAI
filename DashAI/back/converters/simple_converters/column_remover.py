from typing import TYPE_CHECKING

from DashAI.back.converters.base_converter import BaseConverter
from DashAI.back.converters.category.basic_preprocessing import (
    BasicPreprocessingConverter,
)
from DashAI.back.core.schema_fields.base_schema import BaseSchema
from DashAI.back.core.utils import MultilingualString
from DashAI.back.types.dashai_data_type import DashAIDataType
from DashAI.back.types.value_types import Text

if TYPE_CHECKING:
    from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset


class ColumnRemoverSchema(BaseSchema):
    """Schema for ColumnRemover (no configurable hyperparameters)."""


class ColumnRemover(BasicPreprocessingConverter, BaseConverter):
    """Remove the columns selected in scope from the dataset.

    The columns to be deleted are determined by the scope selection in the
    converter job UI: whichever columns are in scope will be removed when
    ``transform`` is called.
    """

    SCHEMA = ColumnRemoverSchema
    DESCRIPTION = MultilingualString(
        en="Removes the columns selected in scope from the dataset.",
        es="Elimina las columnas seleccionadas en el alcance del conjunto de datos.",
        pt="Remove as colunas selecionadas no escopo do conjunto de dados.",
        de="Entfernt die im Geltungsbereich ausgewählten Spalten aus dem Datensatz.",
        zh="从数据集中删除范围内选中的列。",
    )
    SHORT_DESCRIPTION = MultilingualString(
        en="Removes the columns selected in scope from the dataset.",
        es="Elimina las columnas seleccionadas en el alcance del conjunto de datos.",
        pt="Remove as colunas selecionadas no escopo do conjunto de dados.",
        de="Entfernt die im Geltungsbereich ausgewählten Spalten aus dem Datensatz.",
        zh="从数据集中删除范围内选中的列。",
    )
    DISPLAY_NAME = MultilingualString(
        en="Column Remover",
        es="Removedor de Columnas",
        pt="Removedor de Colunas",
        de="Spalten-Entferner",
        zh="列移除器",
    )
    IMAGE_PREVIEW = "column_remover.png"

    metadata = {
        "allowed_types": [],
        "allowed_dtypes": [],
    }

    def __init__(self):
        """Initialise the column remover and set up state.

        The column names to be removed are populated during :meth:`fit`.
        """
        super().__init__()
        self.columns = []

    def fit(self, x: "DashAIDataset", y: "DashAIDataset" = None) -> "ColumnRemover":
        """Record the column names that will be removed during ``transform``.

        Parameters
        ----------
        x : DashAIDataset
            The scoped dataset whose column names are the ones to be removed.
        y : DashAIDataset, optional
            Ignored. Defaults to None.

        Returns
        -------
        ColumnRemover
            The fitted converter instance (self).
        """
        self.columns = x.column_names
        return self

    def transform(
        self, x: "DashAIDataset", y: "DashAIDataset" = None
    ) -> "DashAIDataset":
        """Remove the columns stored during ``fit`` from the dataset.

        Parameters
        ----------
        x : DashAIDataset
            The dataset to remove columns from.
        y : DashAIDataset, optional
            Ignored. Defaults to None.

        Returns
        -------
        DashAIDataset
            The dataset with the fitted columns removed.

        Raises
        ------
        ValueError
            If any fitted column is not present in ``x``.
        """
        missing = [col for col in self.columns if col not in x.column_names]
        if missing:
            raise ValueError(
                f"Cannot remove columns that do not exist in the dataset: {missing}"
            )

        return x.remove_columns(self.columns)

    def get_output_type(self, column_name: str = None) -> DashAIDataType:
        """Return a placeholder type
        (this converter removes columns, not transforms them).

        Parameters
        ----------
        column_name : str, optional
            Not used. Defaults to None.

        Returns
        -------
        DashAIDataType
            A Text placeholder backed by ``pyarrow.string()``.
        """
        import pyarrow as pa

        return Text(arrow_type=pa.string())
