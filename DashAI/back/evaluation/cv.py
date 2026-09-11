"""Cross-validation: several train and validation pairs, scored per fold."""

from DashAI.back.evaluation.base_evaluation_strategy import BaseEvaluationStrategy


class FoldEvaluationStrategy(BaseEvaluationStrategy):
    """Carve the dataset into folds and score each of them.

    Each fold is split into a train and a validation partition, so the scores
    obtained by resampling are validation estimates. When the session reserved
    rows, the kept model is fitted on everything the folds could use and scored
    once against those reserved rows -- the only data no fold and no trial ever
    saw.

    A run carved this way is prepared by ``PrepareAndFoldUnit`` and fitted by
    ``FitModelOverFoldsUnit``, or by ``FitModelOverNestedFoldsUnit`` when the
    run also asks for a search inside each fold.

    The levels a fold run records, which is why the enum has more of them than
    a holdout run needs: ``FOLD`` per fold, aggregated to ``LAST`` with a
    standard deviation; ``TRIAL`` once per trial of a search, holding the mean
    over that trial's folds; and, for a nested run, ``OUTER_FOLD`` aggregated
    to ``LAST_OUTER``, kept apart because it answers a different question --
    how the procedure does rather than how this model does.
    """

    KIND: str = "cv"


class CrossValidationEvaluationStrategy(FoldEvaluationStrategy):
    """Score a model across folds, recording train and validation for each.

    The ordinary cross-validation evaluation. Not offered for
    ``ForecastingTask``, whose folds have no in-sample score to report;
    ``ForecastingCrossValidationEvaluationStrategy`` handles that.
    """

    COMPATIBLE_COMPONENTS = [
        "TabularClassificationTask",
        "TextClassificationTask",
        "ImageClassificationTask",
        "TranslationTask",
        "RegressionTask",
    ]
