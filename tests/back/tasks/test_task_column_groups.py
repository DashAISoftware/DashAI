"""Tests for the per-group column contract shared by every task."""

import pandas as pd
import pytest

from DashAI.back.dataloaders.classes.dashai_dataset import (
    to_dashai_dataset,
    transform_dataset_with_schema,
)
from DashAI.back.tasks.base_task import BaseTask
from DashAI.back.types.categorical import Categorical
from DashAI.back.types.value_types import Date, Float, Integer

SCHEMA = {
    "date": {"type": "Date", "dtype": "%Y-%m-%d"},
    "other_date": {"type": "Date", "dtype": "%Y-%m-%d"},
    "price": {"type": "Float", "dtype": "float64"},
    "units": {"type": "Integer", "dtype": "int64"},
    "note": {"type": "Text", "dtype": "string"},
}

DATES = ["2026-01-01", "2026-01-02", "2026-01-03"]


def _dataset(**columns):
    frame = pd.DataFrame(columns)
    return transform_dataset_with_schema(
        to_dashai_dataset(frame), {name: SCHEMA[name] for name in frame.columns}
    )


class _GroupedTask(BaseTask):
    """One date, at least one number, and a single numeric target."""

    metadata = {
        "inputs": [
            {"types": [Date], "cardinality": 1},
            {"types": [Float, Integer], "cardinality": {"min": 1, "max": "n"}},
        ],
        "outputs": [{"types": [Float, Integer], "cardinality": 1}],
    }

    def num_labels(self, dataset, output_column):
        return None


class _FlatTask(BaseTask):
    """A task written against the older two-key contract."""

    metadata = {
        "inputs_types": [Float, Integer, Categorical],
        "outputs_types": [Float, Integer],
        "inputs_cardinality": "n",
        "outputs_cardinality": 1,
    }

    def num_labels(self, dataset, output_column):
        return None


def test_each_group_gets_the_columns_of_its_own_types():
    dataset = _dataset(date=DATES, price=[1.0, 2.0, 3.0], units=[1, 2, 3])

    prepared = _GroupedTask().prepare_for_task(dataset, ["date", "units"], ["price"])

    assert len(prepared) == 3


def test_a_group_takes_as_many_columns_as_its_maximum_allows():
    dataset = _dataset(date=DATES, price=[1.0, 2.0, 3.0], units=[1, 2, 3])

    prepared = _GroupedTask().prepare_for_task(
        dataset, ["date", "price", "units"], ["price"]
    )

    assert len(prepared) == 3


def test_a_missing_group_is_rejected_even_though_the_total_would_fit():
    dataset = _dataset(date=DATES, other_date=DATES, price=[1.0, 2.0, 3.0])

    with pytest.raises(ValueError, match="Input cardinality"):
        _GroupedTask().prepare_for_task(dataset, ["date", "other_date"], ["price"])


def test_a_group_over_its_maximum_is_rejected():
    dataset = _dataset(date=DATES, other_date=DATES, price=[1.0, 2.0, 3.0])

    with pytest.raises(ValueError, match="Input cardinality"):
        _GroupedTask().prepare_for_task(
            dataset, ["date", "other_date", "price"], ["price"]
        )


def test_a_group_under_its_minimum_is_rejected():
    dataset = _dataset(date=DATES, price=[1.0, 2.0, 3.0])

    with pytest.raises(ValueError, match="Input cardinality"):
        _GroupedTask().prepare_for_task(dataset, ["date"], ["price"])


def test_a_type_in_no_group_is_rejected():
    dataset = _dataset(date=DATES, note=["a", "b", "c"], price=[1.0, 2.0, 3.0])

    with pytest.raises(TypeError):
        _GroupedTask().prepare_for_task(dataset, ["date", "note"], ["price"])


def test_the_error_names_the_group_that_is_short():
    dataset = _dataset(date=DATES, price=[1.0, 2.0, 3.0])

    with pytest.raises(ValueError, match="Float, Integer"):
        _GroupedTask().prepare_for_task(dataset, ["date"], ["price"])


def test_the_metadata_reports_both_the_groups_and_the_flat_view():
    metadata = _GroupedTask.get_metadata()

    assert metadata["inputs"] == [
        {"types": ["Date"], "min": 1, "max": 1},
        {"types": ["Float", "Integer"], "min": 1, "max": "n"},
    ]
    assert metadata["outputs"] == [{"types": ["Float", "Integer"], "min": 1, "max": 1}]
    assert metadata["inputs_types"] == ["Date", "Float", "Integer"]
    assert metadata["inputs_cardinality"] == "n"
    assert metadata["outputs_cardinality"] == 1


def test_a_task_on_the_older_contract_reads_as_a_single_group():
    metadata = _FlatTask.get_metadata()

    assert metadata["inputs"] == [
        {"types": ["Float", "Integer", "Categorical"], "min": 0, "max": "n"}
    ]
    assert metadata["inputs_cardinality"] == "n"
    assert metadata["outputs"] == [{"types": ["Float", "Integer"], "min": 1, "max": 1}]
    assert metadata["outputs_cardinality"] == 1


def test_the_older_contract_still_validates_the_way_it_did():
    dataset = _dataset(price=[1.0, 2.0, 3.0], units=[1, 2, 3], note=["a", "b", "c"])

    with pytest.raises(TypeError):
        _FlatTask().prepare_for_task(dataset, ["price", "note"], ["units"])

    with pytest.raises(ValueError, match="Output cardinality"):
        _FlatTask().prepare_for_task(dataset, ["price"], ["units", "price"])


def test_a_single_group_error_does_not_name_its_types():
    dataset = _dataset(price=[1.0, 2.0, 3.0], units=[1, 2, 3])

    with pytest.raises(ValueError, match="Output cardinality") as raised:
        _FlatTask().prepare_for_task(dataset, ["price"], ["units", "price"])

    assert "for columns of type" not in str(raised.value)
