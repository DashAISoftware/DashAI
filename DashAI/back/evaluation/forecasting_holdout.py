"""Holdout evaluation for models that forecast a series from its own history."""

from DashAI.back.core.enums.metrics import SplitEnum
from DashAI.back.evaluation.holdout import SinglePartitionEvaluationStrategy


class ForecastingHoldoutEvaluationStrategy(SinglePartitionEvaluationStrategy):
    """Holdout evaluation that records no in-sample metrics.

    One thing the ordinary holdout strategy assumes is wrong for a forecaster,
    and it is a decision about evaluation rather than about any model.

    **The training partition is not scored.** Scoring it would mean asking the
    model about dates it was fitted on. That is an in-sample fit statistic,
    which is a real diagnostic but is not comparable with a forecast made
    several steps out; showing the two side by side in one results table
    invites exactly that comparison. Only validation and test are recorded.

    **The kept model is fitted on the training partition alone**, like every
    other holdout run, and nothing is fed to it afterwards. Two approaches that
    would have changed that were tried and dropped, both because they hand the
    model data from a partition it was meant to be held out from:

        refitting through validation before scoring test, which overwrote the
        fit the validation metrics came from, so the saved model could not
        reproduce its own results table;

        advancing the model through the observed validation rows at predict
        time, which re-estimates nothing but still lets a held out partition
        reach the model, which no other task in DashAI does.

    So the two columns describe different horizons, and deliberately:

        validation metrics  <- forecasting 1..len(val) past the fit
        test metrics        <- forecasting len(val)+1..len(val)+len(test),
                               its own forecasts standing in for validation

    The test column is therefore the harder question, not the same one further
    along. Comparing like with like over a chosen horizon is what
    ``RollingOriginSplitter`` is for, since its ``horizon`` says outright how
    many steps ahead each refit is scored on.

    Hyperparameter search is untouched. Its trials are scored on validation, so
    they must not be fitted on it.
    """

    COMPATIBLE_COMPONENTS = ["ForecastingTask"]
    SCORED_SPLITS: tuple = (SplitEnum.VALIDATION, SplitEnum.TEST)
