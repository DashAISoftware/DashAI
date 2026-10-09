from typing import TYPE_CHECKING, List

from DashAI.back.tasks.base_task import BaseTask
from DashAI.back.types.categorical import Categorical
from DashAI.back.types.dashai_value import DashAIValue

if TYPE_CHECKING:
    from numpy import ndarray

    from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset


class ClassificationTask(BaseTask):
    """Abstract base task for all classification problems in DashAI.

    Classification tasks map input features to a finite set of discrete class
    labels. This base class defines the compatible metric components (accuracy,
    precision, recall, F1, etc.) and the output-type constraint (all output
    columns must carry the ``Categorical`` type). Concrete subclasses specialise
    the input/output type metadata and may override ``prepare_for_task`` to add
    task-specific validation.
    """

    COMPATIBLE_COMPONENTS = [
        "Accuracy",
        "BalancedAccuracy",
        "Precision",
        "Recall",
        "F1",
        "CohenKappa",
        "HammingDistance",
        "LogLoss",
        "ROCAUC",
    ]

    metadata: dict = {
        "inputs_types": [DashAIValue],
        "outputs_types": [Categorical],
        "inputs_cardinality": "n",
        "outputs_cardinality": 1,
    }

    def process_predictions(
        self, dataset: "DashAIDataset", predictions: "ndarray", output_column: str
    ) -> "ndarray":
        """Process the predictions to return the class labels.

        Parameters
        ----------
        dataset : DashAIDataset
            Dataset used for training
        predictions : np.ndarray
            Predictions from the model (probabilities for each class)
        output_column : str
            Output column

        Returns
        -------
        np.ndarray
            Processed predictions with class labels
        """
        import numpy as np

        predictions = np.argmax(predictions, axis=1)

        output_type = dataset.types.get(output_column)

        if isinstance(output_type, Categorical):
            return np.array([output_type.int2str(idx) for idx in predictions])
        return np.array(predictions)

    def prepare_for_task(
        self,
        dataset: "DashAIDataset",
        input_columns: List[str],
        output_columns: List[str],
    ) -> "DashAIDataset":
        """Prepare a dataset for a classification task.

        Delegates to the base class for type validation and conversion, then
        verifies that every output column carries a ``Categorical`` type, which
        is required for classification targets.

        Parameters
        ----------
        dataset : DashAIDataset
            The dataset to prepare.  Can be a plain ``DatasetDict`` or an
            already-converted ``DashAIDataset``.
        input_columns : List[str]
            Names of the columns to be used as model inputs.
        output_columns : List[str]
            Names of the columns to be used as classification targets.  Each
            must have a ``Categorical`` type.

        Returns
        -------
        DashAIDataset
            The validated and type-checked dataset, ready for training or
            inference.
        """
        dashai_dataset = super().prepare_for_task(
            dataset, input_columns, output_columns
        )

        for column in output_columns:
            column_type = dashai_dataset.types.get(column)
            if isinstance(column_type, Categorical):
                continue
        return dashai_dataset

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
        output_type = dataset.types.get(output_column)
        if isinstance(output_type, Categorical):
            return output_type.num_categories()
        return None
