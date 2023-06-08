import numpy as np
from sklearn.metrics import recall_score

from DashAI.back.metrics.classification_metric import (
    ClassificationMetric,
    validate_inputs,
)


class Recall(ClassificationMetric):
    """
    Recall metric to classification tasks
    """

    @staticmethod
    def score(true_labels: list, probs_pred_labels: list):
        """Calculates the recall between true labels and predicted labels

        Parameters
        ----------
        true_labels : list
            True labels
        probs_pred_labels : list
            Probabilities of belonging to the class according to the model

        Returns
        -------
        float
            recall score between true labels and predicted labels
        """
        validate_inputs(true_labels, probs_pred_labels)
        pred_labels = np.argmax(probs_pred_labels, axis=1)
        multiclass = len(np.unique(true_labels)) > 2
        if multiclass:
            return recall_score(true_labels, pred_labels, average="micro")
        else:
            return recall_score(true_labels, pred_labels, average="binary")
