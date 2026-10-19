"""What a run records, declared per strategy.

These classes used to run the training too: ``execute`` took the run row and the
database session and did the fitting, the search, the scoring, the aggregation
and the persistence behind one method. That work is the units' now -- see
``FitModelUnit``, ``FitModelOverFoldsUnit`` and their siblings -- and what is
left here is what was underneath it all along: a declaration of how a run is
carved and which partitions it records a score for.

**They stay registered even though they no longer do anything.** The frontend
reads them in four places, and only one is about metrics:

- the session wizard lists them so the user can choose one, and
  ``ModelSession.evaluation_strategy`` is NOT NULL, so without that listing a
  session cannot be created at all;
- it starts on the first one whose ``kind`` is holdout;
- ``kind`` decides the shape of the splits payload and which controls are shown;
- ``scored_splits`` tells the metric charts which partitions exist to plot.

There is precedent for a class in this codebase that declares and does not
execute: ``BaseSplitter.PARTITIONING`` and ``explainable_partitions`` are read
the same way, by the backend and by the frontend, and nothing calls them to do
work.
"""

from typing import Final

from DashAI.back.core.enums.metrics import SplitEnum


class BaseEvaluationStrategy:
    """How a run is carved, and what it records.

    Subclasses declare; none of them execute.
    """

    TYPE: Final[str] = "EvaluationStrategy"

    #: Whether this strategy splits the dataset once or into folds. It decides
    #: which unit prepares the data, because the two publish different shapes,
    #: and which controls the session wizard offers.
    KIND: str = "holdout"

    #: The partitions a run records a score for. Not the same as which
    #: partitions have metrics configured: a forecaster has training metrics
    #: and still must not be judged on the dates it was fitted on, because an
    #: in-sample fit statistic is not comparable with a forecast. A screen that
    #: offers one control per partition reads this instead of assuming all
    #: three exist.
    SCORED_SPLITS: tuple = (SplitEnum.TRAIN, SplitEnum.VALIDATION, SplitEnum.TEST)

    #: The partition the kept model was fitted on, which is what decides which
    #: partitions of a finished run can still be predicted.
    FINAL_FIT_PARTITIONS: tuple = ("train",)

    @classmethod
    def get_metadata(cls) -> dict:
        """Describe the strategy for the frontend.

        Returns
        -------
        dict
            Mapping with ``kind``, which says whether this strategy splits the
            dataset once or into folds, and ``scored_splits``, the partitions
            it writes metrics for.
        """
        return {
            "kind": cls.KIND,
            "scored_splits": [split.value for split in cls.SCORED_SPLITS],
        }
