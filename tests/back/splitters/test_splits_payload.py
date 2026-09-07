from DashAI.back.splitters.holdout import HoldoutSplitter
from DashAI.back.splitters.splits_payload import (
    normalize_splits_payload,
    schema_placeholder_defaults,
)


def test_legacy_seed_becomes_random_state():
    payload = {"splitter_name": "HoldoutSplitter", "seed": 7, "train": 0.6}
    assert normalize_splits_payload(payload)["random_state"] == 7


def test_explicit_random_state_wins_over_seed():
    payload = {"seed": 7, "random_state": 13}
    assert normalize_splits_payload(payload)["random_state"] == 13


def test_legacy_index_lists_move_to_splitted_indexes():
    payload = {
        "splitter_name": "HoldoutSplitter",
        "splitType": "manual",
        "train": [0, 1, 2],
        "test": [3],
        "validation": [4],
    }
    result = normalize_splits_payload(payload)
    assert result["splitted_indexes"] == {
        "train_indexes": [0, 1, 2],
        "test_indexes": [3],
        "val_indexes": [4],
    }
    assert "train" not in result
    assert "test" not in result
    assert "validation" not in result


def test_legacy_index_lists_default_split_type_to_manual():
    payload = {"train": [0, 1], "test": [2], "validation": []}
    assert normalize_splits_payload(payload)["splitType"] == "manual"


def test_new_payload_is_unchanged_and_idempotent():
    payload = {
        "splitter_name": "HoldoutSplitter",
        "splitType": "random",
        "train": 0.6,
        "test": 0.2,
        "validation": 0.2,
        "stratify": False,
        "shuffle": True,
        "random_state": 42,
    }
    once = normalize_splits_payload(payload)
    assert once == payload
    assert normalize_splits_payload(once) == payload


def test_missing_splitter_name_defaults_to_holdout():
    payload = {"train": 0.6, "test": 0.2, "validation": 0.2, "seed": 42}
    assert normalize_splits_payload(payload)["splitter_name"] == "HoldoutSplitter"


def test_null_splitter_name_defaults_to_holdout():
    payload = {"splitter_name": None, "train": 0.6}
    assert normalize_splits_payload(payload)["splitter_name"] == "HoldoutSplitter"


def test_normalize_does_not_mutate_input():
    payload = {"seed": 7}
    normalize_splits_payload(payload)
    assert payload == {"seed": 7}


def test_schema_placeholder_defaults_reads_placeholders():
    defaults = schema_placeholder_defaults(HoldoutSplitter)
    assert defaults == {
        "train": 0.6,
        "test": 0.2,
        "validation": 0.2,
        "stratify": False,
        "shuffle": True,
        "random_state": 42,
    }
