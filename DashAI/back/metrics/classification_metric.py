from typing import Tuple

import numpy as np

from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset
from DashAI.back.metrics.base_metric import BaseMetric


class ClassificationMetric(BaseMetric):
    """Class for metrics associated to classification models."""

    COMPATIBLE_COMPONENTS = [
        "TabularClassificationTask",
        "ImageClassificationTask",
        "TextClassificationTask",
    ]


def validate_inputs(true_labels: np.ndarray, pred_labels: np.ndarray) -> None:
    """Validate inputs.

    Parameters
    ----------
    true_labels : ndarray
        True labels.
    pred_labels : list
        Predict labels by the model.
    """
    if len(true_labels) != len(pred_labels):
        raise ValueError(
            "The length of the true labels and the predicted labels must be equal, "
            f"given: len(true_labels) = {len(true_labels)} and "
            f"len(pred_labels) = {len(pred_labels)}."
        )


def prepare_to_metric(
    dataset: DashAIDataset,
    probs_pred_labels: np.ndarray,
) -> Tuple[np.ndarray, np.ndarray]:
    """Prepare true and prediced labels to be used later in metrics.

    Parameters
    ----------
    dataset : DashAIDataset
        A dashai dataset with labels included.
    probs_pred_labels : np.ndarray
        A two-dimensional matrix in which each column represents a class and the row
        values represent the probability that an example belongs to the class
        associated with the column.

    Returns
    -------
    Tuple[np.ndarray, np.ndarray]
        A tuple with the true and predicted labels in numpy format.
    """
    output_column = dataset.outputs_columns[0]
    true_labels = np.array(dataset[output_column])
    validate_inputs(true_labels, probs_pred_labels)
    pred_labels = np.argmax(probs_pred_labels, axis=1)
    return true_labels, pred_labels
