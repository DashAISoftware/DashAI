import numpy as np
from sklearn.metrics import f1_score

from DashAI.back.metrics.classification_metric import (
    ClassificationMetric,
    prepare_to_metric,
)


class F1(ClassificationMetric):
    """
    F1 score to classification tasks
    """

    @staticmethod
    def score(true_labels: list, probs_pred_labels: list):
        """Calculates the f1 score between true labels and predicted labels

        Parameters
        ----------
        true_labels : list
            True labels
        probs_pred_labels : list
            Probabilities of belonging to the class according to the model

        Returns
        -------
        float
            f1 score between true labels and predicted labels
        """
        true_labels, pred_labels = prepare_to_metric(true_labels, probs_pred_labels)
        multiclass = len(np.unique(true_labels)) > 2
        if multiclass:
            return f1_score(true_labels, pred_labels, average="micro")
        else:
            return f1_score(true_labels, pred_labels, average="binary")
