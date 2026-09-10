import pytest

from DashAI.back.splitters.group_k_fold import GroupKFoldSplitter
from DashAI.back.splitters.k_fold import KFoldSplitter
from DashAI.back.splitters.repeated_k_fold import RepeatedKFoldSplitter
from DashAI.back.splitters.repeated_stratified_k_fold import (
    RepeatedStratifiedKFoldSplitter,
)
from DashAI.back.splitters.stratified_group_k_fold import StratifiedGroupKFoldSplitter
from DashAI.back.splitters.stratified_k_fold import StratifiedKFoldSplitter

FOLD_SPLITTERS = [
    KFoldSplitter,
    StratifiedKFoldSplitter,
    GroupKFoldSplitter,
    StratifiedGroupKFoldSplitter,
    RepeatedKFoldSplitter,
    RepeatedStratifiedKFoldSplitter,
]


@pytest.mark.parametrize("splitter_cls", FOLD_SPLITTERS)
def test_n_splits_is_bounded(splitter_cls):
    n_splits = splitter_cls.get_schema()["properties"]["n_splits"]
    assert n_splits["minimum"] == 2
    assert n_splits["maximum"] == 20


@pytest.mark.parametrize(
    "splitter_cls", [RepeatedKFoldSplitter, RepeatedStratifiedKFoldSplitter]
)
def test_n_repeats_is_bounded(splitter_cls):
    n_repeats = splitter_cls.get_schema()["properties"]["n_repeats"]
    assert n_repeats["minimum"] == 2
    assert n_repeats["maximum"] == 10
