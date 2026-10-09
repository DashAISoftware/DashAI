from typing import TYPE_CHECKING

from DashAI.back.metrics.base_metric import BaseMetric

if TYPE_CHECKING:
    import numpy as np

    from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset


class RegressionMetric(BaseMetric):
    """Base class for all regression evaluation metrics.

    Subclasses implement :meth:`score` to quantify the difference between
    continuous predicted values and ground-truth targets. By default
    regression metrics are minimised (``MAXIMIZE = False``) because smaller
    error values indicate better performance.

    Compatible with DashAI regression tasks. The helper ``prepare_to_metric``
    in this module converts ``DashAIDataset`` targets and raw numpy predictions
    to flat numpy arrays before passing them to sklearn metric functions.
    """

    MAXIMIZE: bool = False
    # ForecastingTask measures the same thing: a continuous prediction against
    # a continuous truth. Listing it here is what makes MAE, RMSE and the rest
    # available to forecasting runs without reimplementing any of them.
    COMPATIBLE_COMPONENTS = ["RegressionTask", "ForecastingTask"]


def prepare_to_metric(
    y: "DashAIDataset",
    y_pred: "np.ndarray",
) -> tuple["np.ndarray", "np.ndarray"]:
    """
    Prepare true and predicted values for metric calculation.

    Parameters
    ----------
    y : DashAIDataset
        True values.
    y_pred : np.ndarray
        Predicted values by the model.

    Returns
    -------
    tuple[np.ndarray, np.ndarray]
        Tuple containing true values and predicted values as numpy arrays.
    """
    import numpy as np

    true_values = np.array(y.to_pandas().to_numpy().flatten())
    pred_values = np.array(y_pred).flatten()

    return true_values, pred_values
