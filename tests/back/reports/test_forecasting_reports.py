"""Unit tests for the forecasting evaluation reports."""

import json

import numpy as np
import pytest

from DashAI.back.core.artifacts import normalize_artifacts
from DashAI.back.reports.base_report import BaseReport
from DashAI.back.reports.forecasting.forecast_vs_actual import ForecastVsActual
from DashAI.back.reports.forecasting.residual_autocorrelation import (
    ResidualAutocorrelation,
)
from DashAI.back.reports.forecasting.residuals_over_time import ResidualsOverTime


@pytest.fixture
def forecasting_data():
    """A trending series and a forecast that tracks it with noise."""
    rng = np.random.default_rng(0)
    steps = np.arange(30)
    y_true = 5 + 2 * steps + rng.normal(0, 1, 30)
    y_pred = y_true + rng.normal(0, 0.5, 30)
    return y_true, y_pred


def _figure(artifact):
    assert artifact.type == "plotly"
    return json.loads(artifact.payload)


def test_forecast_vs_actual_has_actual_and_forecast_traces(forecasting_data):
    y_true, y_pred = forecasting_data

    figure = _figure(ForecastVsActual().compute(y_true, y_pred)[0])

    names = [trace["name"] for trace in figure["data"]]
    assert names == ["Actual", "Forecast"]
    # The observation axis is row order, since reports never see the dates.
    assert list(figure["data"][0]["x"]) == list(range(len(y_true)))
    assert list(figure["data"][0]["y"]) == pytest.approx(list(y_true))
    assert list(figure["data"][1]["y"]) == pytest.approx(list(y_pred))


def test_residuals_over_time_centers_on_truth_minus_forecast(forecasting_data):
    y_true, y_pred = forecasting_data

    figure = _figure(ResidualsOverTime().compute(y_true, y_pred)[0])

    residual_trace = figure["data"][1]
    assert residual_trace["mode"] == "markers"
    assert np.mean(residual_trace["y"]) == pytest.approx(
        np.mean(y_true - y_pred), abs=1e-9
    )
    assert len(residual_trace["x"]) == len(y_true)


def test_residual_autocorrelation_reports_each_lag(forecasting_data):
    y_true, y_pred = forecasting_data

    figure = _figure(ResidualAutocorrelation(max_lag=5).compute(y_true, y_pred)[0])

    bar = figure["data"][0]
    assert bar["type"] == "bar"
    assert list(bar["x"]) == [1, 2, 3, 4, 5]

    residuals = np.asarray(y_true - y_pred, dtype=float)
    centered = residuals - residuals.mean()
    denom = centered @ centered
    expected = [(centered[k:] @ centered[:-k]) / denom for k in range(1, 6)]
    assert list(bar["y"]) == pytest.approx(expected, abs=1e-9)


def test_every_forecasting_report_output_normalizes(forecasting_data):
    y_true, y_pred = forecasting_data

    outputs = [
        ForecastVsActual().compute(y_true, y_pred),
        ResidualsOverTime().compute(y_true, y_pred),
        ResidualAutocorrelation().compute(y_true, y_pred),
    ]
    for output in outputs:
        for item in normalize_artifacts(output):
            assert item["type"] in {"plotly", "table", "text", "image", "grouped"}


def test_forecasting_reports_are_registered_for_the_task():
    for report in (ForecastVsActual, ResidualsOverTime, ResidualAutocorrelation):
        assert report.TYPE == "Report"
        assert issubclass(report, BaseReport)
        assert report.COMPATIBLE_COMPONENTS == ["ForecastingTask"]
