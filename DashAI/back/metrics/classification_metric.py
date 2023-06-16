import numpy as np
from numpy import ndarray

from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset
from DashAI.back.metrics.base_metric import BaseMetric


class ClassificationMetric(BaseMetric):
    """
    Class for metrics associated to classification models
    """

    COMPATIBLE_COMPONENTS = [
        "TabularClassificationTask",
        "ImageClassificationTask",
        "TextClassificationTask",
    ]


def validate_inputs(true_labels: ndarray, pred_labels: list):
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


def prepare_to_metric(true_labels: DashAIDataset, probs_pred_labels: list):
    """Format labels to be used in metrics

    Parameters
    ----------
    true_labels : DashAIDataset
        True labels
    probs_pred_labels : list
        Probabilities of belonging to the class according to the model

    Returns
    -------
    tuple
        A tuple with the true and predicted labels in numpy format
    """
    output_column = true_labels.outputs_columns[0]
    true_labels = np.array(true_labels[output_column])
    validate_inputs(true_labels, probs_pred_labels)
    pred_labels = np.argmax(probs_pred_labels, axis=1)
    return true_labels, pred_labels
