"""Base class for models trained with target columns."""

from abc import abstractmethod
from typing import TYPE_CHECKING

from DashAI.back.models.base_model import BaseModel

if TYPE_CHECKING:
    from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset


class SupervisedModel(BaseModel):
    """Base contract for supervised models in DashAI.

    Supervised models are trained with input features and target columns. The
    metric methods they are scored with -- ``calculate_metrics``,
    ``compute_metrics``, ``_score_split`` and ``_save_metrics`` -- are
    inherited from ``BaseModel`` and are not redefined here: there is exactly
    one definition of each, so every caller scores the same way and the filter
    that drops non-finite scores applies to all of them.
    """

    @abstractmethod
    def train(
        self,
        x_train: "DashAIDataset",
        y_train: "DashAIDataset",
        x_validation: "DashAIDataset" = None,
        y_validation: "DashAIDataset" = None,
    ) -> "BaseModel":
        """Train the model with supervised input features and targets.

        Parameters
        ----------
        x_train : DashAIDataset
            The input features for training.
        y_train : DashAIDataset
            The target labels for training.
        x_validation : DashAIDataset, optional
            Input features for
            validation. Defaults to None.
        y_validation : DashAIDataset, optional
            Target labels for
            validation. Defaults to None.

        Returns
        -------
        BaseModel
            The trained model instance.
        """
        raise NotImplementedError
