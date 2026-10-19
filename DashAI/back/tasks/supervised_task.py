"""Base task for supervised model."""

from typing import TYPE_CHECKING

from numpy import ndarray

from DashAI.back.tasks.base_task import BaseTask

if TYPE_CHECKING:
    from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset


class SupervisedTask(BaseTask):
    """Base class for tasks trained with input and target columns."""

    REQUIRES_TARGET = True

    def num_labels(self, dataset: "DashAIDataset", output_column: str) -> int | None:
        """Return the number of unique labels in the output column for supervised tasks.

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

    def process_predictions(
        self, dataset: "DashAIDataset", predictions: "ndarray", output_column: str
    ):
        """Process the predictions.
        Return predictions unchanged unless a supervised task specializes them.

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
