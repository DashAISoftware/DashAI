import pandas as pd
import pytest

from DashAI.back.dataloaders.classes.dashai_dataset import (
    to_dashai_dataset,
    transform_dataset_with_schema,
)
from DashAI.back.exploration.explorers.time_index_audit import TimeIndexAuditExplorer

DATE_FORMAT = "%Y-%m-%d"


class _Explorer:
    """Stand-in for the Explorer database record the explorers receive."""

    def __init__(self, columns, name=""):
        self.id = 1
        self.name = name
        self.columns = [{"columnName": col} for col in columns]


def _dataset(dates):
    frame = pd.DataFrame({"date": list(dates)})
    schema = {"date": {"type": "Date", "dtype": DATE_FORMAT}}
    return transform_dataset_with_schema(to_dashai_dataset(frame), schema)


def _audit(dates):
    """Run the audit and hand back the report as a plain dict."""
    explorer = TimeIndexAuditExplorer()
    report = explorer.launch_exploration(_dataset(dates), _Explorer(["date"]))
    return dict(zip(report["metric"], report["value"], strict=True))


def _grid(freq, periods=24):
    return pd.date_range("2020-01-01", periods=periods, freq=freq).strftime(DATE_FORMAT)


@pytest.mark.parametrize(
    "freq",
    ["D", "W", "B", "MS", "ME", "QS", "YS"],
    ids=[
        "daily",
        "weekly",
        "business",
        "month-start",
        "month-end",
        "quarterly",
        "yearly",
    ],
)
def test_a_clean_calendar_grid_is_regularly_spaced(freq):
    # A month is 28 to 31 days long and a quarter 89 to 92, so consecutive gaps
    # differ on every calendar spacing but the daily and the weekly one. Judging
    # regularity by gap length would call a clean monthly series irregular and
    # send the user off to resample a table that needs nothing.
    report = _audit(_grid(freq))

    assert report["Regularly spaced"] == "Yes"
    assert report["Missing periods"] == 0
    assert report["Duplicate dates"] == 0


def test_a_series_that_ends_off_the_grid_is_not_regularly_spaced():
    # The grid a 7 day spacing builds over these dates stops at the 15th, so
    # nothing is missing from it, yet the 20th sits on no weekly grid.
    report = _audit(["2020-01-01", "2020-01-08", "2020-01-15", "2020-01-20"])

    assert report["Regularly spaced"] == "No"


def test_a_hole_in_the_grid_is_counted_and_reported():
    dates = list(_grid("D", periods=10)) + list(_grid("D", periods=30)[15:])

    report = _audit(dates)

    assert report["Regularly spaced"] == "No"
    assert report["Missing periods"] == 5
    assert report["Largest gap (days)"] == 6


def test_a_repeated_date_is_counted_and_breaks_regularity():
    dates = list(_grid("D", periods=10)) + ["2020-01-01"]

    report = _audit(dates)

    assert report["Regularly spaced"] == "No"
    assert report["Duplicate dates"] == 1
    assert report["Missing periods"] == 0


def test_rows_without_a_date_are_reported_apart_from_the_grid():
    dates = list(_grid("D", periods=10)) + [None, ""]

    report = _audit(dates)

    assert report["Observations"] == 12
    assert report["Rows without a date"] == 2
    assert report["Regularly spaced"] == "Yes"


def test_a_series_too_short_to_have_a_spacing_leaves_it_unanswered():
    report = _audit(["2020-01-01", "2020-01-02"])

    assert report["Inferred frequency"] == "Unknown"
    assert report["Missing periods"] is None
    assert report["Largest gap (days)"] is None


def test_the_audit_needs_a_date_column():
    frame = pd.DataFrame({"sales": [1.0, 2.0]})
    dataset = transform_dataset_with_schema(
        to_dashai_dataset(frame), {"sales": {"type": "Float", "dtype": "float64"}}
    )

    with pytest.raises(ValueError, match="needs a Date column"):
        TimeIndexAuditExplorer().launch_exploration(dataset, _Explorer(["sales"]))
