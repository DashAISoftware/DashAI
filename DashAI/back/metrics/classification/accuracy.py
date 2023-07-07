import numpy as np
from sklearn.metrics import accuracy_score

from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset
from DashAI.back.metrics.classification_metric import (
    ClassificationMetric,
    prepare_to_metric,
)


class Accuracy(ClassificationMetric):
    """
    Accuracy metric to classification tasks
    """

    @staticmethod
    def score(true_labels: DashAIDataset, probs_pred_labels: np.ndarray) -> float:
        """Calculates the accuracy between true labels and predicted labels

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
            Accuracy score between true labels and predicted labels
        """
        true_labels, pred_labels = prepare_to_metric(true_labels, probs_pred_labels)
        return accuracy_score(true_labels, pred_labels)
