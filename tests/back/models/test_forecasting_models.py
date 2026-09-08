import numpy as np
import pandas as pd
import pytest

from DashAI.back.dataloaders.classes.dashai_dataset import (
    to_dashai_dataset,
    transform_dataset_with_schema,
)
from DashAI.back.models.forecasting.arima import ARIMA
from DashAI.back.models.forecasting.base_forecasting_model import ForecastingModel
from DashAI.back.models.forecasting.exponential_smoothing import ExponentialSmoothing
from DashAI.back.models.forecasting.naive import NaiveForecaster
from DashAI.back.models.forecasting.seasonal_naive import SeasonalNaiveForecaster

ALL_MODELS = [NaiveForecaster, SeasonalNaiveForecaster, ARIMA, ExponentialSmoothing]


def _dates(n):
    return [f"2026-{1 + i // 28:02d}-{1 + i % 28:02d}" for i in range(n)]


def _x(n):
    return transform_dataset_with_schema(
        to_dashai_dataset(pd.DataFrame({"date": _dates(n)})),
        {"date": {"type": "Date", "dtype": "%Y-%m-%d"}},
    )


def _y(values):
    return to_dashai_dataset(pd.DataFrame({"target": [float(v) for v in values]}))


def _fit(model, values):
    model._trained_on = len(values)
    return model.train(_x(len(values)), _y(values))


def _future(model, steps):
    """The dates that follow the training data, which is all these models forecast.

    Predicting is date driven rather than row driven: a model works out how far
    past the end of training each requested date falls. Handing it the first
    rows of the series would be asking for a fit, not a forecast, and is
    refused.
    """
    trained_on = model._trained_on
    return transform_dataset_with_schema(
        to_dashai_dataset(
            pd.DataFrame({"date": _dates(trained_on + steps)[trained_on:]})
        ),
        {"date": {"type": "Date", "dtype": "%Y-%m-%d"}},
    )


# --- the shared contract -----------------------------------------------------


@pytest.mark.parametrize("model_class", ALL_MODELS)
def test_every_model_forecasts_one_value_per_requested_row(model_class):
    model = model_class()
    _fit(model, list(range(1, 31)))

    forecast = model.predict(_future(model, 4))

    assert len(forecast) == 4
    assert np.isfinite(np.asarray(forecast, dtype=float)).all()


@pytest.mark.parametrize("model_class", ALL_MODELS)
def test_every_model_is_declared_for_the_forecasting_task(model_class):
    assert "ForecastingTask" in model_class.COMPATIBLE_COMPONENTS
    assert issubclass(model_class, ForecastingModel)


@pytest.mark.parametrize("model_class", ALL_MODELS)
def test_every_model_round_trips_through_save_and_load(model_class, tmp_path):
    model = model_class()
    _fit(model, list(range(1, 31)))
    expected = list(np.asarray(model.predict(_future(model, 3)), dtype=float))

    path = tmp_path / "model.joblib"
    model.save(str(path))
    restored = model_class.load(str(path))

    restored_forecast = np.asarray(restored.predict(_future(model, 3)), dtype=float)

    assert list(restored_forecast) == pytest.approx(expected)


@pytest.mark.parametrize("model_class", ALL_MODELS)
def test_predicting_before_training_is_refused(model_class):
    with pytest.raises(ValueError, match="train"):
        model_class().predict(_x(2))


# --- the baselines, whose answers are exactly knowable ------------------------


def test_naive_carries_the_last_value_forward():
    model = NaiveForecaster()
    _fit(model, [10.0, 20.0, 35.0])

    assert list(model.predict(_future(model, 3))) == pytest.approx([35.0, 35.0, 35.0])


def test_naive_on_a_flat_series_predicts_that_constant():
    model = NaiveForecaster()
    _fit(model, [7.0] * 10)

    assert list(model.predict(_future(model, 4))) == pytest.approx([7.0] * 4)


def test_seasonal_naive_repeats_the_last_season():
    model = SeasonalNaiveForecaster(season_length=4)
    _fit(model, [1.0, 2.0, 3.0, 4.0, 10.0, 20.0, 30.0, 40.0])

    # The last full season is 10, 20, 30, 40, and it repeats from there.
    assert list(model.predict(_future(model, 6))) == pytest.approx(
        [10.0, 20.0, 30.0, 40.0, 10.0, 20.0]
    )


def test_seasonal_naive_with_a_season_of_one_is_the_naive_forecast():
    model = SeasonalNaiveForecaster(season_length=1)
    _fit(model, [10.0, 20.0, 35.0])

    assert list(model.predict(_future(model, 2))) == pytest.approx([35.0, 35.0])


def test_seasonal_naive_needs_a_full_season_of_history():
    model = SeasonalNaiveForecaster(season_length=12)

    with pytest.raises(ValueError, match="season"):
        _fit(model, [1.0, 2.0, 3.0])


# --- the statsmodels wrappers ------------------------------------------------


def test_arima_follows_a_linear_trend():
    # A perfectly linear series with a first difference is something ARIMA
    # should extrapolate almost exactly.
    model = ARIMA(p=1, d=1, q=0)
    _fit(model, list(range(1, 41)))

    forecast = np.asarray(model.predict(_future(model, 3)), dtype=float)

    assert forecast == pytest.approx([41.0, 42.0, 43.0], abs=0.5)


def test_exponential_smoothing_tracks_the_level_of_a_flat_series():
    model = ExponentialSmoothing()
    _fit(model, [5.0] * 30)

    forecast = np.asarray(model.predict(_future(model, 3)), dtype=float)

    assert forecast == pytest.approx([5.0, 5.0, 5.0], abs=0.1)


def test_exponential_smoothing_can_use_a_seasonal_component():
    season = [10.0, 20.0, 30.0, 40.0]
    model = ExponentialSmoothing(seasonal="add", season_length=4)
    _fit(model, season * 8)

    forecast = np.asarray(model.predict(_future(model, 4)), dtype=float)

    assert forecast == pytest.approx(season, abs=1.0)
