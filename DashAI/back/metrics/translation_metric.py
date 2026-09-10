from typing import TYPE_CHECKING

from DashAI.back.metrics.base_metric import BaseMetric

if TYPE_CHECKING:
    import numpy as np

    from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset


class TranslationMetric(BaseMetric):
    """Base class for all machine-translation evaluation metrics.

    Subclasses implement :meth:`score` to measure the similarity between
    model-generated translations and reference translations. Translation
    metrics operate on lists of strings rather than numeric arrays.

    Compatible with DashAI translation tasks. The helper ``prepare_to_metric``
    in this module extracts the reference strings from a ``DashAIDataset``
    and pairs them with the predicted translation strings before passing them
    to the underlying metric library (e.g. ``evaluate``, ``torchmetrics``).
    """

    COMPATIBLE_COMPONENTS = ["TranslationTask"]


def prepare_to_metric(
    y: "DashAIDataset",
    y_pred: "np.ndarray",
) -> tuple["np.ndarray", "np.ndarray"]:
    """Prepare data for metric calculation.

    Parameters
    ----------
    y : DashAIDataset
        True labels.
    y_pred : ndarray
        Predicted labels by the model.

    Returns
    -------
    tuple[ndarray, ndarray]
        Prepared true and predicted labels.

    Raises
    ------
    ValueError
        If the lengths of true and predicted labels do not match.
    """
    import numpy as np

    column_name = y.column_names[0]
    true = np.array(y[column_name])
    pred = y_pred

    if len(true) != len(pred):
        raise ValueError(
            "The length of the true labels and the predicted labels must be equal, "
            f"given: len(true_labels) = {len(true)} and "
            f"len(pred_labels) = {len(pred)}."
        )

    return true, pred
