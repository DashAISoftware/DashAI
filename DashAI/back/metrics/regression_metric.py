from typing import Tuple

import numpy as np

from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset
from DashAI.back.metrics.base_metric import BaseMetric


class RegressionMetric(BaseMetric):
    """Class for metrics associated with regression models."""

    COMPATIBLE_COMPONENTS = ["RegressionTask"]


def validate_inputs(true_values: np.ndarray, pred_values: np.ndarray) -> None:
    """Validate inputs.

    Parameters
    ----------
    true_values : ndarray
        True values.
    pred_values : ndarray
        Predicted values by the model.
    """
    if len(true_values) != len(pred_values):
        raise ValueError(
            "The length of the true and the predicted values must be equal, "
            f"given: len(true_values) = {len(true_values)} and "
            f"len(pred_values) = {len(pred_values)}."
        )


def prepare_to_metric(
    y: DashAIDataset, predicted_values: np.ndarray
) -> Tuple[np.ndarray, np.ndarray]:
    """Prepare true and predicted values to be used later in metrics.

    Parameters
    ----------
    y : DashAIDataset
        A DashAIDataset with the output columns of the data.
    predicted_values: np.ndarray
        A one-dimensional array with the predicted values for each instance.

    Returns
    -------
    Tuple[np.ndarray, np.ndarray]
        A tuple with the true and predicted values in numpy format.
    """
    column_name = y.column_names[0]
    true_values = np.array(y[column_name])
    validate_inputs(true_values, predicted_values)
    return true_values, predicted_values
