"""A forecasting dataset has to be in date order before anything else happens.

Row order is taken as time order everywhere downstream: the temporal splitter
carves partitions by position, and the models hand statsmodels the values in
row order. Neither checks, so a file that is not sorted by its date column
produces partitions that are not periods of time and a model fitted on a
scrambled series, with nothing reporting a problem.

Sorting belongs to the task: it sees the whole dataset and knows which column
is the date, and it runs before the split. The splitter cannot do it, because
on the windowed route it receives lag columns and no date at all.
"""

import pandas as pd
import pytest

from DashAI.back.dataloaders.classes.dashai_dataset import (
    to_dashai_dataset,
    transform_dataset_with_schema,
)
from DashAI.back.tasks.forecasting_task import ForecastingTask

SHUFFLED = ["2020-03-01", "2020-01-01", "2020-04-01", "2020-02-01"]
VALUES = [30.0, 10.0, 40.0, 20.0]


def _dataset(dates, values, date_format="%Y-%m-%d"):
    return transform_dataset_with_schema(
        to_dashai_dataset(pd.DataFrame({"date": dates, "v": values})),
        {
            "date": {"type": "Date", "dtype": date_format},
            "v": {"type": "Float", "dtype": "float64"},
        },
    )


def test_rows_come_back_in_date_order():
    prepared = ForecastingTask().prepare_for_task(
        _dataset(SHUFFLED, VALUES), ["date"], ["v"]
    )

    frame = prepared.to_pandas()
    assert list(frame["date"]) == [
        "2020-01-01",
        "2020-02-01",
        "2020-03-01",
        "2020-04-01",
    ]


def test_the_target_travels_with_its_own_date():
    # The failure that matters: a sort that moved the dates but not the values
    # would silently pair every observation with the wrong day.
    prepared = ForecastingTask().prepare_for_task(
        _dataset(SHUFFLED, VALUES), ["date"], ["v"]
    )

    frame = prepared.to_pandas()
    assert list(frame["v"]) == [10.0, 20.0, 30.0, 40.0]


def test_an_already_sorted_dataset_is_left_as_it_is():
    ordered = ["2020-01-01", "2020-02-01", "2020-03-01", "2020-04-01"]
    values = [10.0, 20.0, 30.0, 40.0]

    prepared = ForecastingTask().prepare_for_task(
        _dataset(ordered, values), ["date"], ["v"]
    )

    frame = prepared.to_pandas()
    assert list(frame["date"]) == ordered
    assert list(frame["v"]) == values


def test_sorting_reads_the_columns_declared_format():
    # Day first dates sort wrongly as text: "01/02/2020" precedes "31/01/2020"
    # alphabetically while following it in time.
    dates = ["31/01/2020", "01/02/2020", "15/01/2020"]
    prepared = ForecastingTask().prepare_for_task(
        _dataset(dates, [31.0, 1.0, 15.0], date_format="%d/%m/%Y"),
        ["date"],
        ["v"],
    )

    frame = prepared.to_pandas()
    assert list(frame["date"]) == ["15/01/2020", "31/01/2020", "01/02/2020"]
    assert list(frame["v"]) == [15.0, 31.0, 1.0]


def test_the_declared_types_survive_the_sort():
    from DashAI.back.types.value_types import Date

    prepared = ForecastingTask().prepare_for_task(
        _dataset(SHUFFLED, VALUES), ["date"], ["v"]
    )

    assert isinstance(prepared.types["date"], Date)
    assert prepared.types["date"].format == "%Y-%m-%d"


def test_an_unreadable_date_is_still_rejected_by_validation():
    # Sorting must not swallow the type checking that ran before it.
    dataset = transform_dataset_with_schema(
        to_dashai_dataset(pd.DataFrame({"note": ["a", "b"], "v": [1.0, 2.0]})),
        {
            "note": {"type": "Text", "dtype": "string"},
            "v": {"type": "Float", "dtype": "float64"},
        },
    )

    with pytest.raises(TypeError):
        ForecastingTask().prepare_for_task(dataset, ["note"], ["v"])
