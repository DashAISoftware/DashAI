"""Base task for unsupervised model."""

from typing import TYPE_CHECKING, Optional

from DashAI.back.tasks.base_task import BaseTask

if TYPE_CHECKING:
    from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset


class UnsupervisedTask(BaseTask):
    """Base class for tasks trained without target columns."""

    REQUIRES_TARGET = False

    def num_labels(
        self, dataset: "DashAIDataset", output_column: Optional[str] = None
    ) -> None:
        """Return ``None``: a task without a target has no labels to count.

        The same answer a supervised task gives when its target is not a set
        of classes, so whatever builds the model reads the count the same way
        for both.

        Parameters
        ----------
        dataset : DashAIDataset
            Dataset used for training.
        output_column : str, optional
            Unused: there is no output column.

        Returns
        -------
        None
        """
        return None
