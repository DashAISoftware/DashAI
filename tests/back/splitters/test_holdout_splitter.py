import pandas as pd
import pytest
from pydantic import ValidationError

from DashAI.back.dataloaders.classes.dashai_dataset import to_dashai_dataset
from DashAI.back.splitters.holdout import HoldoutSplitter, HoldoutSplitterSchema
from DashAI.back.splitters.splits_payload import normalize_splits_payload


@pytest.fixture
def xy():
    dataset = to_dashai_dataset(pd.DataFrame({"a": list(range(10)), "y": [0, 1] * 5}))
    return dataset.select_columns(["a"]), dataset.select_columns(["y"])


def test_manual_payload_uses_given_indexes(xy):
    x, y = xy
    splitter = HoldoutSplitter(
        {
            "splitter_name": "HoldoutSplitter",
            "splitType": "manual",
            "splitted_indexes": {
                "train_indexes": [0, 1, 2, 3, 4, 5],
                "test_indexes": [6, 7],
                "val_indexes": [8, 9],
            },
            "stratify": False,
            "shuffle": True,
            "random_state": 42,
        }
    )
    x_split, _, indices = splitter.split(x, y)

    assert indices["train_indexes"] == [0, 1, 2, 3, 4, 5]
    assert len(x_split["train"]) == 6
    assert len(x_split["test"]) == 2
    assert len(x_split["validation"]) == 2


def test_legacy_manual_payload_splits_after_normalization(xy):
    x, y = xy
    legacy = {
        "splitter_name": "HoldoutSplitter",
        "splitType": "manual",
        "train": [0, 1, 2, 3, 4, 5],
        "test": [6, 7],
        "validation": [8, 9],
    }
    splitter = HoldoutSplitter(normalize_splits_payload(legacy))
    x_split, _, indices = splitter.split(x, y)

    assert indices["test_indexes"] == [6, 7]
    assert len(x_split["train"]) == 6


def test_random_state_from_payload_changes_the_split(xy):
    x, y = xy
    base = {
        "splitType": "random",
        "train": 0.6,
        "test": 0.2,
        "validation": 0.2,
        "stratify": False,
        "shuffle": True,
    }
    first = HoldoutSplitter({**base, "random_state": 1}).split(x, y)[2]
    same = HoldoutSplitter({**base, "random_state": 1}).split(x, y)[2]
    other = HoldoutSplitter({**base, "random_state": 99}).split(x, y)[2]

    assert first["train_indexes"] == same["train_indexes"]
    assert first["train_indexes"] != other["train_indexes"]


def test_schema_rejects_proportions_that_do_not_sum_to_one():
    with pytest.raises(ValidationError):
        HoldoutSplitterSchema.model_validate(
            {
                "train": 0.8,
                "test": 0.2,
                "validation": 0.2,
                "stratify": False,
                "shuffle": True,
                "random_state": 42,
            }
        )


def test_schema_rejects_empty_train_partition():
    with pytest.raises(ValidationError):
        HoldoutSplitterSchema.model_validate(
            {
                "train": 0.0,
                "test": 0.5,
                "validation": 0.5,
                "stratify": False,
                "shuffle": True,
                "random_state": 42,
            }
        )


def test_schema_accepts_the_placeholder_configuration():
    schema = HoldoutSplitterSchema.model_validate(
        {
            "train": 0.6,
            "test": 0.2,
            "validation": 0.2,
            "stratify": False,
            "shuffle": True,
            "random_state": 42,
        }
    )
    assert schema.train == 0.6


def test_proportions_are_plain_numbers_in_the_json_schema():
    train = HoldoutSplitter.get_schema()["properties"]["train"]
    assert train["type"] == "number"
    assert "anyOf" not in train
