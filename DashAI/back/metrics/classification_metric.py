from DashAI.back.metrics.base_metric import BaseMetric


class ClassificationMetric(BaseMetric):
    """
    Class for metrics associated to classification models
    """

    _compatible_tasks = ["TabularClassificationTask"]
