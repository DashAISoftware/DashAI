import numpy as np

from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset
from DashAI.back.metrics.base_metric import BaseMetric


class TranslationMetric(BaseMetric):
    """Class for metrics associated to translation models."""

    COMPATIBLE_COMPONENTS = ["TranslationTask"]


def validate_inputs(true_labels: list, pred_labels: list) -> None:
    """Validate inputs.

    Parameters
    ----------
    true_labels : list
        True labels.
    pred_labels : list
        Predict labels by the model.
    """
    if len(true_labels) != len(pred_labels):
        raise ValueError("The length of the true and predicted labels must be equal.")


def prepare_to_metric(y: DashAIDataset, target_sentences: list):
    """Format labels to be used in metrics.

    Parameters
    ----------
    y : DashAIDataset
        True sentences of the dataset.
    target_sentences : list
        Target sentences.

    Returns
    -------
    tuple
        A tuple with the true and predicted sentences.
    """
    column_name = y.column_names[0]
    source_sentences = np.array(y[column_name])
    validate_inputs(source_sentences, target_sentences)
    return source_sentences, target_sentences
