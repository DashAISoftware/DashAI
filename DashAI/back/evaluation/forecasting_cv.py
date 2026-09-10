"""Cross-validation for models that forecast a series from its own history."""

from DashAI.back.core.enums.metrics import SplitEnum
from DashAI.back.evaluation.cv import FoldEvaluationStrategy


class ForecastingCrossValidationEvaluationStrategy(FoldEvaluationStrategy):
    """Rolling origin cross-validation that records no in-sample metrics.

    Only one thing separates this from the ordinary cross-validation
    strategy: the training partition of a fold is not scored. Scoring it would
    mean asking the model about dates it was fitted on, which is a fit
    statistic rather than a forecast and is not comparable with the validation
    score of the same fold.

    Nothing else needs to change, and that is worth stating because it was not
    obvious. Each fold already trains on everything before its own validation
    window, and the final refit already uses the whole pool of rows outside
    the reserved tail, so this strategy never had the horizon problem that
    holdout did. Pair it with ``RollingOriginSplitter``, whose folds walk the
    origin forward through time.
    """

    COMPATIBLE_COMPONENTS = ["ForecastingTask"]
    SCORED_SPLITS: tuple = (SplitEnum.VALIDATION, SplitEnum.TEST)
