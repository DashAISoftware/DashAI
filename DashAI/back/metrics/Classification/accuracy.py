import numpy as np
from sklearn.metrics import accuracy_score

from DashAI.back.metrics.classification_metric import ClassificationMetric


class Accuracy(ClassificationMetric):
    """
    Accuracy metric to classification tasks
    """

    @staticmethod
    def score(true_labels: list, probs_pred_labels: list):
        """Calculates the accuracy between true labels and predicted labels

        Parameters
        ----------
        true_labels : list
            True labels
        probs_pred_labels : list
            Probabilities of belonging to the class according to the model

        Returns
        -------
        float
            Accuracy score between true labels and predicted labels
        """
        validate_inputs(true_labels, probs_pred_labels)
        pred_labels = np.argmax(probs_pred_labels, axis=1)
        return accuracy_score(true_labels, pred_labels)


def validate_inputs(true_labels: list, pred_labels: list):
    """Validate inputs.

    Parameters
    ----------
    true_labels : list
        True labels
    pred_labels : list
        Predict labels by the model
    """
    if len(true_labels) != len(pred_labels):
        raise ValueError("The length of the true and predicted labels must be equal.")
