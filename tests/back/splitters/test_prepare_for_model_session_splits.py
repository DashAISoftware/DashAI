import pandas as pd

from DashAI.back.dataloaders.classes.dashai_dataset import (
    prepare_for_model_session,
    to_dashai_dataset,
)


def dataset():
    return to_dashai_dataset(pd.DataFrame({"a": list(range(10)), "y": [0, 1] * 5}))


def test_manual_split_reads_splitted_indexes():
    splits = {
        "splitter_name": "HoldoutSplitter",
        "splitType": "manual",
        "splitted_indexes": {
            "train_indexes": [0, 1, 2, 3, 4, 5],
            "test_indexes": [6, 7],
            "val_indexes": [8, 9],
        },
    }
    prepared, indexes = prepare_for_model_session(dataset(), splits, ["y"])

    assert indexes["train_indexes"] == [0, 1, 2, 3, 4, 5]
    assert len(prepared["test"]) == 2
    assert len(prepared["validation"]) == 2


def test_legacy_manual_split_still_reads_index_lists():
    splits = {
        "splitType": "manual",
        "train": [0, 1, 2, 3, 4, 5],
        "test": [6, 7],
        "validation": [8, 9],
    }
    prepared, indexes = prepare_for_model_session(dataset(), splits, ["y"])

    assert indexes["test_indexes"] == [6, 7]
    assert len(prepared["train"]) == 6


def test_random_split_accepts_random_state_as_the_seed():
    splits = {
        "splitType": "random",
        "train": 0.6,
        "test": 0.2,
        "validation": 0.2,
        "shuffle": True,
        "random_state": 7,
    }
    _, first = prepare_for_model_session(dataset(), splits, ["y"])
    _, again = prepare_for_model_session(dataset(), splits, ["y"])
    _, other = prepare_for_model_session(
        dataset(), {**splits, "random_state": 99}, ["y"]
    )

    assert first["train_indexes"] == again["train_indexes"]
    assert first["train_indexes"] != other["train_indexes"]
