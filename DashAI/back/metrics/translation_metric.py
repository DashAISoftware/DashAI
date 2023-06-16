from DashAI.back.metrics.base_metric import BaseMetric


class TranslationMetric(BaseMetric):
    """
    Class for metrics associated to translation models
    """

    COMPATIBLE_COMPONENTS = ["TranslationTask"]


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
