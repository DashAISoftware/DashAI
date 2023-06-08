from DashAI.back.metrics.base_metric import BaseMetric


class ClassificationMetric(BaseMetric):
    """
    Class for metrics associated to classification models
    """

    COMPATIBLE_COMPONENTS = ["TabularClassificationTask"]


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
