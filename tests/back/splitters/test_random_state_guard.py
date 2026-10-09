"""Every splitter must keep scikit-learn's shuffle and random_state contract.

scikit-learn rejects a non-null ``random_state`` when ``shuffle`` is False, so a
splitter that forwards both unconditionally crashes for any configuration that
turns shuffling off.
"""

import pandas as pd
import pytest

from DashAI.back.dataloaders.classes.dashai_dataset import to_dashai_dataset
from DashAI.back.splitters.group_k_fold import GroupKFoldSplitter
from DashAI.back.splitters.holdout import HoldoutSplitter
from DashAI.back.splitters.k_fold import KFoldSplitter
from DashAI.back.splitters.stratified_group_k_fold import StratifiedGroupKFoldSplitter
from DashAI.back.splitters.stratified_k_fold import StratifiedKFoldSplitter

FOLD_SPLITTERS = [KFoldSplitter, StratifiedKFoldSplitter]
GROUP_SPLITTERS = [GroupKFoldSplitter, StratifiedGroupKFoldSplitter]


@pytest.fixture
def xy():
    dataset = to_dashai_dataset(
        pd.DataFrame(
            {
                "a": list(range(12)),
                "group": [0, 0, 1, 1, 2, 2, 3, 3, 4, 4, 5, 5],
                "y": [0, 1] * 6,
            }
        )
    )
    return dataset.select_columns(["a", "group"]), dataset.select_columns(["y"])


@pytest.mark.parametrize("splitter_cls", FOLD_SPLITTERS + GROUP_SPLITTERS)
def test_shuffle_off_with_a_random_state_still_splits(splitter_cls, xy):
    x, y = xy
    splitter = splitter_cls(
        {
            "n_splits": 3,
            "shuffle": False,
            "random_state": 42,
            "group_column": "group",
        }
    )

    folds = splitter.split_indexes(x, y)

    assert len(folds) == 3


def test_holdout_shuffle_off_with_a_random_state_still_splits(xy):
    x, y = xy
    splitter = HoldoutSplitter(
        {
            "train": 0.6,
            "test": 0.2,
            "validation": 0.2,
            "stratify": False,
            "shuffle": False,
            "random_state": 42,
        }
    )

    train, test, val = splitter.split_indexes(x, y)

    assert len(train) + len(test) + len(val) == 12
    # Without shuffling the partitions keep the original row order.
    assert train == sorted(train)


@pytest.mark.parametrize("splitter_cls", FOLD_SPLITTERS)
def test_shuffle_on_stays_reproducible(splitter_cls, xy):
    x, y = xy
    config = {"n_splits": 3, "shuffle": True, "random_state": 7}

    first = splitter_cls(config).split_indexes(x, y)
    again = splitter_cls(config).split_indexes(x, y)
    other = splitter_cls({**config, "random_state": 99}).split_indexes(x, y)

    assert [f[1].tolist() for f in first] == [f[1].tolist() for f in again]
    assert [f[1].tolist() for f in first] != [f[1].tolist() for f in other]
