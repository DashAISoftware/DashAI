import pandas as pd
import pytest

from DashAI.back.dataloaders.classes.dashai_dataset import (
    to_dashai_dataset,
    transform_dataset_with_schema,
)
from DashAI.back.exploration.explorers.time_series_plot import TimeSeriesPlotExplorer

DATES = ["2026-01-01", "2026-01-02", "2026-01-03", "2026-01-04"]
SALES = [100, 120, 115, 140]
COSTS = [10.5, 12.0, 11.5, 14.0]


class _Explorer:
    """Stand-in for the Explorer database record the explorers receive."""

    def __init__(self, columns, name=""):
        self.id = 1
        self.name = name
        self.columns = [{"columnName": col} for col in columns]


def _dataset(columns=None):
    frame = pd.DataFrame(columns or {"date": DATES, "sales": SALES, "costs": COSTS})
    schema = {
        "date": {"type": "Date", "dtype": "%Y-%m-%d"},
        "sales": {"type": "Integer", "dtype": "int64"},
        "costs": {"type": "Float", "dtype": "float64"},
    }
    schema = {name: schema[name] for name in frame.columns}
    return transform_dataset_with_schema(to_dashai_dataset(frame), schema)


def _spec(**types):
    return {name: {"type": t, "dtype": d} for name, (t, d) in types.items()}


DEFAULT_SPEC = _spec(
    date=("Date", "%Y-%m-%d"),
    sales=("Integer", "int64"),
    costs=("Float", "float64"),
)


def test_plots_one_series_against_time():
    explorer = TimeSeriesPlotExplorer()

    figure = explorer.launch_exploration(_dataset(), _Explorer(["date", "sales"]))

    assert len(figure.data) == 1
    assert list(figure.data[0].y) == SALES


def test_the_time_axis_holds_real_dates_not_text():
    # The whole reason this is not a scatter plot with a Date bolted on: the
    # axis has to be a time axis, which means real datetimes.
    explorer = TimeSeriesPlotExplorer()

    figure = explorer.launch_exploration(_dataset(), _Explorer(["date", "sales"]))

    assert list(figure.data[0].x) == list(pd.to_datetime(DATES))


def test_several_series_share_the_time_axis():
    explorer = TimeSeriesPlotExplorer()

    figure = explorer.launch_exploration(
        _dataset(), _Explorer(["date", "sales", "costs"])
    )

    assert len(figure.data) == 2
    assert {trace.name for trace in figure.data} == {"sales", "costs"}


def test_rows_out_of_order_are_plotted_chronologically():
    order = [2, 0, 3, 1]
    dataset = _dataset(
        {
            "date": [DATES[i] for i in order],
            "sales": [SALES[i] for i in order],
            "costs": [COSTS[i] for i in order],
        }
    )
    explorer = TimeSeriesPlotExplorer()

    figure = explorer.launch_exploration(dataset, _Explorer(["date", "sales"]))

    assert list(figure.data[0].x) == list(pd.to_datetime(DATES))
    assert list(figure.data[0].y) == SALES


def test_a_selection_with_one_date_and_one_number_is_accepted():
    assert TimeSeriesPlotExplorer.validate_columns(
        _Explorer(["date", "sales"]), DEFAULT_SPEC
    )


def test_a_selection_without_a_date_is_rejected():
    assert not TimeSeriesPlotExplorer.validate_columns(
        _Explorer(["sales", "costs"]), DEFAULT_SPEC
    )


def test_a_selection_with_two_dates_is_rejected():
    spec = _spec(
        date=("Date", "%Y-%m-%d"),
        other=("Date", "%Y-%m-%d"),
    )

    assert not TimeSeriesPlotExplorer.validate_columns(
        _Explorer(["date", "other"]), spec
    )


def test_a_selection_without_a_numeric_column_is_rejected():
    spec = _spec(date=("Date", "%Y-%m-%d"), label=("Categorical", "string"))

    assert not TimeSeriesPlotExplorer.validate_columns(
        _Explorer(["date", "label"]), spec
    )


def test_a_single_column_is_rejected():
    assert not TimeSeriesPlotExplorer.validate_columns(
        _Explorer(["date"]), DEFAULT_SPEC
    )


def test_markers_are_off_by_default_and_can_be_turned_on():
    plain = TimeSeriesPlotExplorer().launch_exploration(
        _dataset(), _Explorer(["date", "sales"])
    )
    marked = TimeSeriesPlotExplorer(markers=True).launch_exploration(
        _dataset(), _Explorer(["date", "sales"])
    )

    assert plain.data[0].mode == "lines"
    assert "markers" in marked.data[0].mode


def test_the_explorer_name_overrides_the_title():
    explorer = TimeSeriesPlotExplorer()

    figure = explorer.launch_exploration(
        _dataset(), _Explorer(["date", "sales"], name="Weekly sales")
    )

    assert figure.layout.title.text == "Weekly sales"


def test_a_dataset_whose_dates_do_not_match_their_format_is_refused():
    dataset = _dataset({"date": DATES, "sales": SALES})
    # Claim a layout the values do not follow.
    dataset.types["date"].format = "%d/%m/%Y"
    explorer = TimeSeriesPlotExplorer()

    with pytest.raises(ValueError, match="do not match the date format"):
        explorer.launch_exploration(dataset, _Explorer(["date", "sales"]))
