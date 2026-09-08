import pandas as pd
import pytest

from DashAI.back.dataloaders.classes.dashai_dataset import to_dashai_dataset
from DashAI.back.splitters.rolling_origin import RollingOriginSplitter
from DashAI.back.splitters.temporal_holdout import TemporalHoldoutSplitter


def _xy(n=20):
    x = to_dashai_dataset(pd.DataFrame({"lag_1": list(range(n))}))
    y = to_dashai_dataset(pd.DataFrame({"target": list(range(n))}))
    return x, y


# --- TemporalHoldoutSplitter -------------------------------------------------


def test_holdout_partitions_are_contiguous_and_in_time_order():
    x, y = _xy(20)
    splitter = TemporalHoldoutSplitter({"train": 0.6, "validation": 0.2, "test": 0.2})

    train, test, val = splitter.split_indexes(x, y)

    assert train == list(range(12))
    assert val == list(range(12, 16))
    assert test == list(range(16, 20))


def test_holdout_never_lets_a_later_row_train_an_earlier_one():
    # The whole point: everything trained on precedes everything scored on.
    x, y = _xy(20)
    splitter = TemporalHoldoutSplitter({"train": 0.6, "validation": 0.2, "test": 0.2})

    train, test, val = splitter.split_indexes(x, y)

    assert max(train) < min(val)
    assert max(val) < min(test)


def test_holdout_ignores_a_request_to_shuffle():
    # Shuffling a time series is the mistake this splitter exists to prevent,
    # so a payload asking for it is overruled rather than honoured.
    x, y = _xy(20)
    splitter = TemporalHoldoutSplitter(
        {"train": 0.6, "validation": 0.2, "test": 0.2, "shuffle": True}
    )

    assert splitter.shuffle is False

    train, _, _ = splitter.split_indexes(x, y)
    assert train == sorted(train)


def test_holdout_without_a_test_partition_still_orders_the_rest():
    x, y = _xy(10)
    splitter = TemporalHoldoutSplitter({"train": 0.8, "validation": 0.2, "test": 0.0})

    train, test, val = splitter.split_indexes(x, y)

    assert train == list(range(8))
    assert val == list(range(8, 10))
    assert test == []


def test_holdout_uses_every_row_exactly_once():
    x, y = _xy(17)
    splitter = TemporalHoldoutSplitter({"train": 0.6, "validation": 0.2, "test": 0.2})

    train, test, val = splitter.split_indexes(x, y)

    assert sorted(train + val + test) == list(range(17))


def test_holdout_reports_its_explainable_partitions():
    partitions = TemporalHoldoutSplitter.explainable_partitions(
        {"train_indexes": [0, 1], "test_indexes": [4], "val_indexes": [2, 3]}
    )

    assert partitions == {"train": [0, 1], "test": [4], "val": [2, 3]}


# --- RollingOriginSplitter ---------------------------------------------------


def test_rolling_origin_grows_the_training_window():
    x, y = _xy(10)
    splitter = RollingOriginSplitter(
        {"n_splits": 4, "horizon": 1, "step": 1, "test_size": 0}
    )

    folds = splitter.split_indexes(x, y)

    assert [(list(t), list(v)) for t, v in folds] == [
        (list(range(6)), [6]),
        (list(range(7)), [7]),
        (list(range(8)), [8]),
        (list(range(9)), [9]),
    ]


def test_every_fold_trains_only_on_the_past():
    x, y = _xy(30)
    splitter = RollingOriginSplitter(
        {"n_splits": 5, "horizon": 2, "step": 2, "test_size": 0}
    )

    for train, validation in splitter.split_indexes(x, y):
        assert max(train) < min(validation)


def test_the_horizon_sets_how_many_rows_each_fold_scores():
    x, y = _xy(20)
    splitter = RollingOriginSplitter(
        {"n_splits": 3, "horizon": 3, "step": 1, "test_size": 0}
    )

    for _, validation in splitter.split_indexes(x, y):
        assert len(validation) == 3


def test_the_step_sets_how_far_the_origin_moves():
    x, y = _xy(20)
    splitter = RollingOriginSplitter(
        {"n_splits": 3, "horizon": 1, "step": 4, "test_size": 0}
    )

    folds = splitter.split_indexes(x, y)
    origins = [len(train) for train, _ in folds]

    assert [origins[i + 1] - origins[i] for i in range(len(origins) - 1)] == [4, 4]


def test_the_reserved_test_rows_are_the_tail_of_the_series():
    # A random carve would scatter future rows through every fold's training
    # data, which is the leak this strategy exists to close.
    x, y = _xy(20)
    splitter = RollingOriginSplitter(
        {"n_splits": 3, "horizon": 1, "step": 1, "test_size": 0.2}
    )

    test_rows, pool = splitter._carve_test_split(x, y)

    assert test_rows == [16, 17, 18, 19]
    assert pool == list(range(16))


def test_an_impossible_combination_names_a_knob():
    x, y = _xy(6)
    splitter = RollingOriginSplitter(
        {"n_splits": 5, "horizon": 3, "step": 2, "test_size": 0}
    )

    with pytest.raises(ValueError, match="n_splits|horizon|step"):
        splitter.split_indexes(x, y)


def test_folds_map_back_to_original_rows_after_a_carve():
    # split_indexes works in pool positions; FoldSplitter maps them back. With
    # a tail carve the pool is the head, so the mapping must stay in order.
    x, y = _xy(20)
    splitter = RollingOriginSplitter(
        {"n_splits": 3, "horizon": 1, "step": 1, "test_size": 0.2}
    )

    _, _, indices = splitter.split(x, y)

    assert indices["full_dataset"]["test_indexes"] == [16, 17, 18, 19]
    for name, fold in indices.items():
        if name == "full_dataset":
            continue
        assert max(fold["train_indexes"]) < min(fold["validation_indexes"])
        assert max(fold["validation_indexes"]) < 16
