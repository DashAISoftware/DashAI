"""Which partitions of a run its saved model can actually be asked to predict.

For most tasks that is every partition the run has: a fitted classifier will
happily label the rows it was trained on. A forecaster cannot. It answers "how
far past the end of training is this date", so any row inside the window it was
fitted through has no forecast to give, only a fit. Which rows those are
depends on the evaluation strategy: a holdout run fits on the training
partition and can forecast everything after it, while the folds of a rolling
origin run walk through everything outside the reserved tail.
"""

from DashAI.back.evaluation.forecasting_cv import (
    ForecastingCrossValidationEvaluationStrategy,
)
from DashAI.back.evaluation.forecasting_holdout import (
    ForecastingHoldoutEvaluationStrategy,
)
from DashAI.back.evaluation.holdout import HoldoutEvaluationStrategy
from DashAI.back.splitters.holdout import HoldoutSplitter
from DashAI.back.splitters.rolling_origin import RollingOriginSplitter
from DashAI.back.splitters.splits_payload import predictable_splits
from DashAI.back.splitters.temporal_holdout import TemporalHoldoutSplitter
from DashAI.back.tasks.forecasting_task import ForecastingTask
from DashAI.back.tasks.tabular_classification_task import TabularClassificationTask

TEMPORAL_RUN = {
    "train_indexes": [0, 1, 2, 3, 4, 5],
    "val_indexes": [6, 7],
    "test_indexes": [8, 9],
}

ROLLING_RUN = {
    "fold_0": {"train_indexes": [0, 1, 2, 3], "test_indexes": [4, 5]},
    "full_dataset": {
        "train_indexes": [0, 1, 2, 3, 4, 5, 6, 7],
        "test_indexes": [8, 9],
    },
}

SHUFFLED_RUN = {
    "train_indexes": [0, 1, 2, 3, 4, 5],
    "val_indexes": [6, 7],
    "test_indexes": [8, 9],
}


def registry_for(splitter, task, strategy):
    """Build the smallest mapping the resolver needs."""
    return {
        splitter.__name__: {"class": splitter},
        task.__name__: {"class": task},
        strategy.__name__: {"class": strategy},
    }


def test_forecasting_holdout_offers_every_partition_after_training():
    registry = registry_for(
        TemporalHoldoutSplitter,
        ForecastingTask,
        ForecastingHoldoutEvaluationStrategy,
    )

    assert predictable_splits(
        {"splitter_name": "TemporalHoldoutSplitter"},
        TEMPORAL_RUN,
        registry,
        task_name="ForecastingTask",
        evaluation_strategy="ForecastingHoldoutEvaluationStrategy",
    ) == [{"name": "test", "rows": 2}, {"name": "val", "rows": 2}]


def test_forecasting_holdout_without_rows_after_training_offers_nothing():
    registry = registry_for(
        TemporalHoldoutSplitter,
        ForecastingTask,
        ForecastingHoldoutEvaluationStrategy,
    )

    assert (
        predictable_splits(
            {"splitter_name": "TemporalHoldoutSplitter"},
            {"train_indexes": [0, 1, 2, 3], "val_indexes": [], "test_indexes": []},
            registry,
            task_name="ForecastingTask",
            evaluation_strategy="ForecastingHoldoutEvaluationStrategy",
        )
        == []
    )


def test_rolling_origin_offers_only_the_reserved_tail():
    registry = registry_for(
        RollingOriginSplitter,
        ForecastingTask,
        ForecastingCrossValidationEvaluationStrategy,
    )

    assert predictable_splits(
        {"splitter_name": "RollingOriginSplitter"},
        ROLLING_RUN,
        registry,
        task_name="ForecastingTask",
        evaluation_strategy="ForecastingCrossValidationEvaluationStrategy",
    ) == [{"name": "test", "rows": 2}]


def test_an_ordinary_task_keeps_every_partition_and_the_whole_dataset():
    registry = registry_for(
        HoldoutSplitter,
        TabularClassificationTask,
        HoldoutEvaluationStrategy,
    )

    assert predictable_splits(
        {"splitter_name": "HoldoutSplitter"},
        SHUFFLED_RUN,
        registry,
        task_name="TabularClassificationTask",
        evaluation_strategy="HoldoutEvaluationStrategy",
    ) == [
        {"name": "train", "rows": 6},
        {"name": "test", "rows": 2},
        {"name": "val", "rows": 2},
        {"name": "all", "rows": 10},
    ]


def test_an_unregistered_task_is_treated_as_an_ordinary_one():
    registry = {"HoldoutSplitter": {"class": HoldoutSplitter}}

    assert predictable_splits(
        {"splitter_name": "HoldoutSplitter"},
        SHUFFLED_RUN,
        registry,
        task_name="APluginTask",
        evaluation_strategy="APluginStrategy",
    ) == [
        {"name": "train", "rows": 6},
        {"name": "test", "rows": 2},
        {"name": "val", "rows": 2},
        {"name": "all", "rows": 10},
    ]
