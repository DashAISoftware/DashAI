import pandas as pd
import pytest

from DashAI.back.converters.simple_converters.time_series_window import (
    TimeSeriesWindowConverter,
)
from DashAI.back.dataloaders.classes.dashai_dataset import (
    to_dashai_dataset,
    transform_dataset_with_schema,
)
from DashAI.back.types.value_types import Float, Integer

# The example from the brief, as dates a Date column can actually hold.
DATES = [
    "2026-01-01",
    "2026-01-02",
    "2026-01-03",
    "2026-01-04",
    "2026-01-05",
    "2026-01-06",
]
SALES = [100, 120, 115, 140, 150, 160]


def _dataset(columns, schema):
    return transform_dataset_with_schema(
        to_dashai_dataset(pd.DataFrame(columns)), schema
    )


def _series(dates=None, sales=None, sales_type="Integer", sales_dtype="int64"):
    dataset = _dataset(
        {
            "date": dates if dates is not None else DATES,
            "sales": sales if sales is not None else SALES,
        },
        {
            "date": {"type": "Date", "dtype": "%Y-%m-%d"},
            "sales": {"type": sales_type, "dtype": sales_dtype},
        },
    )
    return dataset.select_columns(["date"]), dataset.select_columns(["sales"])


def _apply(converter, x, y):
    return converter.fit(x, y).transform(x, y)


def test_builds_the_windowed_table_from_the_brief():
    x, y = _series()

    result = _apply(TimeSeriesWindowConverter(window_size=3), x, y)

    assert result.column_names == ["lag_3", "lag_2", "lag_1", "target"]
    assert result.to_pandas().to_numpy().tolist() == [
        [100, 120, 115, 140],
        [120, 115, 140, 150],
        [115, 140, 150, 160],
    ]


def test_the_date_column_and_everything_else_is_dropped():
    x, y = _series()

    result = _apply(TimeSeriesWindowConverter(window_size=3), x, y)

    assert "date" not in result.column_names
    assert "sales" not in result.column_names


def test_rows_out_of_order_give_the_same_answer_as_sorted_rows():
    order = [3, 0, 5, 1, 4, 2]
    x, y = _series(dates=[DATES[i] for i in order], sales=[SALES[i] for i in order])

    result = _apply(TimeSeriesWindowConverter(window_size=3), x, y)

    assert result.to_pandas().to_numpy().tolist() == [
        [100, 120, 115, 140],
        [120, 115, 140, 150],
        [115, 140, 150, 160],
    ]


def test_an_integer_series_keeps_integer_columns():
    x, y = _series()

    result = _apply(TimeSeriesWindowConverter(window_size=3), x, y)

    assert isinstance(result.types["lag_1"], Integer)
    assert isinstance(result.types["target"], Integer)


def test_a_float_series_gives_float_columns():
    x, y = _series(
        sales=[float(v) for v in SALES], sales_type="Float", sales_dtype="float64"
    )

    result = _apply(TimeSeriesWindowConverter(window_size=3), x, y)

    assert isinstance(result.types["lag_1"], Float)
    assert isinstance(result.types["target"], Float)


def test_a_window_of_one_still_works():
    x, y = _series()

    result = _apply(TimeSeriesWindowConverter(window_size=1), x, y)

    assert result.column_names == ["lag_1", "target"]
    assert result.to_pandas().to_numpy().tolist() == [
        [100, 120],
        [120, 115],
        [115, 140],
        [140, 150],
        [150, 160],
    ]


def test_a_missing_target_is_refused():
    x, _ = _series()

    with pytest.raises(ValueError, match="target"):
        TimeSeriesWindowConverter(window_size=3).fit(x, None)


def test_a_non_numeric_target_is_refused():
    dataset = _dataset(
        {"date": DATES, "label": ["a", "b", "c", "d", "e", "f"]},
        {
            "date": {"type": "Date", "dtype": "%Y-%m-%d"},
            "label": {"type": "Text", "dtype": "string"},
        },
    )

    with pytest.raises(ValueError, match="Text"):
        TimeSeriesWindowConverter(window_size=3).fit(
            dataset.select_columns(["date"]), dataset.select_columns(["label"])
        )


def test_a_scope_without_exactly_one_date_is_refused():
    dataset = _dataset(
        {"date": DATES, "other": DATES, "sales": SALES},
        {
            "date": {"type": "Date", "dtype": "%Y-%m-%d"},
            "other": {"type": "Date", "dtype": "%Y-%m-%d"},
            "sales": {"type": "Integer", "dtype": "int64"},
        },
    )

    with pytest.raises(ValueError, match="one Date"):
        TimeSeriesWindowConverter(window_size=3).fit(
            dataset.select_columns(["date", "other"]),
            dataset.select_columns(["sales"]),
        )


def test_duplicate_dates_are_refused():
    x, y = _series(dates=[DATES[0]] + DATES[:5])

    with pytest.raises(ValueError, match="repeated dates"):
        _apply(TimeSeriesWindowConverter(window_size=3), x, y)


def test_a_window_that_leaves_no_complete_row_is_refused():
    x, y = _series()

    with pytest.raises(ValueError, match="window"):
        _apply(TimeSeriesWindowConverter(window_size=6), x, y)


def test_an_irregular_series_warns_but_still_produces_rows(capsys):
    # 1st, 2nd, 3rd, then a jump. lag_2 covers a different span for different
    # rows, which the user should know about without being blocked.
    irregular = [
        "2026-01-01",
        "2026-01-02",
        "2026-01-03",
        "2026-02-01",
        "2026-02-02",
        "2026-03-15",
    ]
    x, y = _series(dates=irregular)

    result = _apply(TimeSeriesWindowConverter(window_size=3), x, y)

    assert len(result) == 3
    assert "irregular" in capsys.readouterr().out.lower()


def test_a_missing_date_is_refused():
    # A row with no date sorts to the end, so its value would be windowed as
    # the most recent point of the series rather than wherever it belongs.
    # The converter already refuses repeated dates for the same reason.
    x, y = _series(dates=[DATES[0], None] + DATES[2:])

    with pytest.raises(ValueError, match="no date"):
        _apply(TimeSeriesWindowConverter(window_size=3), x, y)


def test_a_column_of_no_dates_at_all_is_refused():
    # The worst version of the same thing: nothing left to sort by, so the
    # rows would be windowed in whatever order the file happened to hold.
    x, y = _series(dates=[None] * len(DATES))

    with pytest.raises(ValueError, match="no date"):
        _apply(TimeSeriesWindowConverter(window_size=3), x, y)


def test_a_gap_in_the_series_is_refused():
    # An integer series used to fail the int64 cast with a message about
    # non-finite values, and a float one used to hand the model NaN lags.
    x, y = _series(sales=[100, 120, None, 140, 150, 160])

    with pytest.raises(ValueError, match="no value"):
        _apply(TimeSeriesWindowConverter(window_size=3), x, y)


def test_a_gap_in_a_float_series_is_refused_too():
    x, y = _series(
        sales=[100.0, 120.0, None, 140.0, 150.0, 160.0],
        sales_type="Float",
        sales_dtype="float64",
    )

    with pytest.raises(ValueError, match="no value"):
        _apply(TimeSeriesWindowConverter(window_size=3), x, y)
