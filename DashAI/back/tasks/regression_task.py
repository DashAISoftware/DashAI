from typing import TYPE_CHECKING, List, Union

from DashAI.back.core.utils import MultilingualString
from DashAI.back.tasks.base_task import BaseTask
from DashAI.back.types.categorical import Categorical
from DashAI.back.types.value_types import Float, Integer

if TYPE_CHECKING:
    from datasets import DatasetDict
    from numpy import ndarray

    from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset


class RegressionTask(BaseTask):
    """Abstract base task for continuous-output (regression) problems in DashAI.

    Regression tasks predict one or more continuous numeric values from input
    features. This base class constrains output columns to ``Float`` or
    ``Integer`` types and accepts ``Float``, ``Integer``, and ``Categorical``
    input types. Unlike classification tasks, regression does not require a
    ``Categorical`` output and ``num_labels`` always returns ``None``.
    """

    DESCRIPTION: str = MultilingualString(
        en="Predict continuous numeric values from tabular data.",
        es="Predice valores numéricos continuos a partir de datos tabulares.",
        pt="Prevê valores numéricos contínuos a partir de dados tabulares.",
        de="Kontinuierliche numerische Werte aus tabellarischen Daten vorhersagen.",
        zh="从表格数据中预测连续数值。",
    )
    DISPLAY_NAME: str = MultilingualString(
        en="Regression", es="Regresión", pt="Regressão", de="Regression", zh="回归"
    )

    metadata: dict = {
        "inputs_types": [Float, Integer, Categorical],
        "outputs_types": [Float, Integer],
        "inputs_cardinality": "n",
        "outputs_cardinality": 1,
    }

    def prepare_for_task(
        self,
        dataset: Union["DatasetDict", "DashAIDataset"],
        input_columns: List[str],
        output_columns: List[str],
    ) -> "DashAIDataset":
        """Convert the dataset to DashAIDataset and validate types.


        A copy of the dataset is created.

        Parameters
        ----------
        datasetdict : DatasetDict
            Dataset to be changed

        Returns
        -------
        DashAIDataset
            Dataset with validated types
        """
        dashai_dataset = super().prepare_for_task(
            dataset, input_columns, output_columns
        )
        return dashai_dataset

    def process_predictions(
        self, dataset: "DashAIDataset", predictions: "ndarray", output_column: str
    ):
        """Process the predictions

        Parameters
        ----------
        dataset : DashAIDataset
            Dataset used for training
        predictions : np.ndarray
            Predictions from the model
        output_column : str
            Output column

        Returns
        -------
        Processed predictions
        """
        return predictions

    def num_labels(self, dataset: "DashAIDataset", output_column: str) -> int | None:
        """Get the number of unique labels in the output column.

        Parameters
        ----------
        dataset : DashAIDataset
            Dataset used for training
        output_column : str
            Output column

        Returns
        -------
        int | None
            Number of unique labels or None if not applicable
        """
        return None
