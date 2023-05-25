import numpy as np
from sklearn.metrics import accuracy_score

from DashAI.back.metrics.classification_metric import ClassificationMetric


class Accuracy(ClassificationMetric):
    """
    Accuracy metric to classification tasks
    """

    @staticmethod
    def score(true, probs_pred, *args):
        pred = np.argmax(probs_pred, axis=1)
        return accuracy_score(true, pred, *args)
