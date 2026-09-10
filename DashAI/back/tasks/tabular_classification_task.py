from typing import TYPE_CHECKING, List, Union

from DashAI.back.core.utils import MultilingualString
from DashAI.back.tasks.classification_task import ClassificationTask
from DashAI.back.types.categorical import Categorical
from DashAI.back.types.value_types import Float, Integer

if TYPE_CHECKING:
    from datasets import DatasetDict

    from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset


class TabularClassificationTask(ClassificationTask):
    """Task for classifying structured tabular data into discrete categories.

    Tabular classification predicts categorical labels from structured feature
    tables (rows of observations, columns of features). It accepts numeric
    (``Float``, ``Integer``) and categorical (``Categorical``) inputs, requires
    a single categorical output column, and is compatible with all sklearn-based
    and DashAI tabular classifier models.
    """

    DESCRIPTION: str = MultilingualString(
        en="Predict categorical labels from tabular data (rows and columns).",
        es=(
            "Predice etiquetas categóricas a partir de datos tabulares "
            "(filas y columnas)."
        ),
        pt=(
            "Prevê rótulos categóricos a partir de dados tabulares (linhas e colunas)."
        ),
        de=(
            "Kategoriale Zielgrößen aus tabellarischen Daten (Zeilen und Spalten) "
            "vorhersagen."
        ),
        zh="从表格数据（行和列）中预测分类标签。",
    )
    DISPLAY_NAME: str = MultilingualString(
        en="Tabular Classification",
        es="Clasificación Tabular",
        pt="Classificação Tabular",
        de="Tabellarische Klassifikation",
        zh="表格分类",
    )
    metadata: dict = {
        "inputs_types": [Float, Integer, Categorical],
        "outputs_types": [Categorical],
        "inputs_cardinality": "n",
        "outputs_cardinality": 1,
    }

    def prepare_for_task(
        self,
        dataset: Union["DatasetDict", "DashAIDataset"],
        input_columns: List[str],
        output_columns: List[str],
    ) -> "DashAIDataset":
        """Convert the dataset to DashAIDataset and check the columns types

        A copy of the dataset is created.

        Parameters
        ----------
        dataset : Union[DatasetDict, DashAIDataset]
            Dataset to be changed

        Returns
        -------
        DashAIDataset
            Dataset with the new types
        """
        dashai_dataset = super().prepare_for_task(
            dataset, input_columns, output_columns
        )
        return dashai_dataset
