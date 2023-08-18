"""DashAI precision classification metric implementation."""
import numpy as np
from sklearn.metrics import precision_score

from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset
from DashAI.back.metrics.classification_metric import (
    ClassificationMetric,
    prepare_to_metric,
)


class Precision(ClassificationMetric):
    """Precision metric to classification tasks."""

    @staticmethod
    def score(true_labels: DashAIDataset, probs_pred_labels: np.ndarray) -> float:
        """Calculate precision between true labels and predicted labels.

        Parameters
        ----------
        true_labels : DashAIDataset
            A DashAI dataset with labels.
        probs_pred_labels : np.ndarray
            A two-dimensional matrix in which each column represents a class
            and the row values represent the probability that an example belongs
            to the class associated with the column.

        Returns
        -------
        float
            Precision score between true labels and predicted labels
        """
        true_labels, pred_labels = prepare_to_metric(true_labels, probs_pred_labels)
        multiclass = len(np.unique(true_labels)) > 2
        if multiclass:
            return precision_score(true_labels, pred_labels, average="macro")
        else:
            return precision_score(true_labels, pred_labels, average="binary")
