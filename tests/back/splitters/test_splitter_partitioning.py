"""The splitter metadata and task gating the frontend resolves splitters from.

Before this, the holdout path in the frontend hardcoded ``HoldoutSplitter``
whatever the task was, so a forecasting session was offered a splitter that
shuffles. Shuffling a series trains a model on its own future and reports a
score it could never reproduce, and nothing about it raises an error. The
frontend now reads both the partitioning and the task compatibility from the
registry, which is what these tests pin.
"""

import pytest

from DashAI.back.splitters.group_k_fold import GroupKFoldSplitter
from DashAI.back.splitters.holdout import HoldoutSplitter
from DashAI.back.splitters.k_fold import KFoldSplitter
from DashAI.back.splitters.rolling_origin import RollingOriginSplitter
from DashAI.back.splitters.temporal_holdout import TemporalHoldoutSplitter

HOLDOUT_SPLITTERS = [HoldoutSplitter, TemporalHoldoutSplitter]
FOLD_SPLITTERS = [KFoldSplitter, GroupKFoldSplitter, RollingOriginSplitter]


@pytest.mark.parametrize("splitter", HOLDOUT_SPLITTERS)
def test_holdout_splitters_report_their_partitioning(splitter):
    assert splitter.get_metadata()["partitioning"] == "holdout"


@pytest.mark.parametrize("splitter", FOLD_SPLITTERS)
def test_fold_splitters_report_their_partitioning(splitter):
    assert splitter.get_metadata()["partitioning"] == "folds"


def test_fold_splitters_keep_reporting_their_inner_splitters():
    # The partitioning key is added alongside what was already there rather
    # than replacing it, since nested CV reads this.
    metadata = KFoldSplitter.get_metadata()

    assert "compatibleInnerSplitters" in metadata
    assert metadata["partitioning"] == "folds"


def test_the_shuffling_holdout_splitter_is_not_offered_for_forecasting():
    # The whole point of the fix: this splitter can shuffle, so forecasting
    # must not be able to reach it.
    assert "ForecastingTask" not in HoldoutSplitter.COMPATIBLE_COMPONENTS


def test_the_shuffling_holdout_splitter_still_serves_every_other_task():
    for task in (
        "TabularClassificationTask",
        "TextClassificationTask",
        "ImageClassificationTask",
        "TranslationTask",
        "RegressionTask",
    ):
        assert task in HoldoutSplitter.COMPATIBLE_COMPONENTS


def test_the_temporal_splitters_are_offered_for_forecasting_alone():
    for splitter in (TemporalHoldoutSplitter, RollingOriginSplitter):
        assert splitter.COMPATIBLE_COMPONENTS == ["ForecastingTask"]


def test_the_temporal_splitter_does_not_inherit_the_other_ones_tasks():
    assert "TabularClassificationTask" not in (
        TemporalHoldoutSplitter.COMPATIBLE_COMPONENTS
    )


def test_forecasting_can_reach_a_holdout_splitter_at_all():
    # If no holdout splitter were compatible, the frontend would resolve None
    # and the holdout strategy would silently stop working for forecasting.
    reachable = [
        splitter
        for splitter in HOLDOUT_SPLITTERS
        if "ForecastingTask" in splitter.COMPATIBLE_COMPONENTS
    ]

    assert reachable == [TemporalHoldoutSplitter]
