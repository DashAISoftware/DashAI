"""Holdout evaluation: one split into three partitions, scored once."""

from DashAI.back.evaluation.base_evaluation_strategy import BaseEvaluationStrategy


class SinglePartitionEvaluationStrategy(BaseEvaluationStrategy):
    """Split once into train, validation and test.

    The training set fits the model, the validation set is what a
    hyperparameter search is measured on, and the test set is scored once at
    the end. A run carved this way is prepared by ``PrepareAndSplitUnit`` and
    fitted by ``FitModelUnit``.
    """

    KIND: str = "holdout"


class HoldoutEvaluationStrategy(SinglePartitionEvaluationStrategy):
    """Split once into train, validation and test, and score all three.

    The ordinary holdout evaluation. Not offered for ``ForecastingTask``:
    scoring the training partition of a forecaster means predicting on dates
    it was fitted on, which is a fit statistic rather than a forecast and does
    not belong in the same results table as one.
    ``ForecastingHoldoutEvaluationStrategy`` records validation and test only.

    The kept model is fitted on the training partition alone in both, so it is
    the model the recorded metrics describe. The validation partition is handed
    to the fit, which models use to watch training and stop early -- being
    given it to watch is not the same as being fitted on it.
    """

    COMPATIBLE_COMPONENTS = [
        "TabularClassificationTask",
        "TextClassificationTask",
        "ImageClassificationTask",
        "TranslationTask",
        "RegressionTask",
    ]
