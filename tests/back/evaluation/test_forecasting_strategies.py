"""Evaluation strategies that know what a forecast is.

What the ordinary strategies assume and a forecaster does not share is the
training partition being worth scoring. For a forecaster that means asking a
model about dates it was fitted on. That is a fit statistic, not a forecast,
and putting the two in one results table invites a comparison that means
nothing.

The final fit is deliberately the ordinary one. Fitting the kept model through
validation puts the validation rows inside its own history, which leaves the
recorded validation metrics belonging to a model that no longer exists and the
validation rows impossible to forecast at all. One fit answers for both
columns instead.
"""

import pandas as pd
import pytest

from DashAI.back.core.enums.metrics import SplitEnum
from DashAI.back.dataloaders.classes.dashai_dataset import (
    select_columns,
    to_dashai_dataset,
    transform_dataset_with_schema,
)
from DashAI.back.evaluation.cv import CrossValidationEvaluationStrategy
from DashAI.back.evaluation.forecasting_cv import (
    ForecastingCrossValidationEvaluationStrategy,
)
from DashAI.back.evaluation.forecasting_holdout import (
    ForecastingHoldoutEvaluationStrategy,
)
from DashAI.back.evaluation.holdout import HoldoutEvaluationStrategy
from DashAI.back.models.forecasting.exponential_smoothing import ExponentialSmoothing
from DashAI.back.splitters.temporal_holdout import TemporalHoldoutSplitter

FORECASTING_STRATEGIES = [
    ForecastingHoldoutEvaluationStrategy,
    ForecastingCrossValidationEvaluationStrategy,
]


def _split(n=60):
    season = [10.0, 20.0, 30.0, 40.0, 35.0, 25.0, 15.0, 12.0, 18.0, 28.0, 38.0, 22.0]
    values = [v + i * 0.8 for i, v in enumerate(season * (n // 12))]
    dates = pd.date_range("2022-01-01", periods=n, freq="MS").strftime("%Y-%m-%d")
    dataset = transform_dataset_with_schema(
        to_dashai_dataset(pd.DataFrame({"date": dates.tolist(), "v": values})),
        {
            "date": {"type": "Date", "dtype": "%Y-%m-%d"},
            "v": {"type": "Float", "dtype": "float64"},
        },
    )
    x, y = select_columns(dataset, ["date"], ["v"])
    return TemporalHoldoutSplitter(
        {"train": 0.6, "validation": 0.2, "test": 0.2}
    ).split(x, y)


# --- what each strategy declares ---------------------------------------------


@pytest.mark.parametrize("strategy", FORECASTING_STRATEGIES)
def test_forecasting_strategies_serve_forecasting(strategy):
    assert strategy.COMPATIBLE_COMPONENTS == ["ForecastingTask"]


def test_the_ordinary_strategies_no_longer_serve_forecasting():
    for strategy in (HoldoutEvaluationStrategy, CrossValidationEvaluationStrategy):
        assert "ForecastingTask" not in strategy.COMPATIBLE_COMPONENTS
        assert "RegressionTask" in strategy.COMPATIBLE_COMPONENTS


def test_each_strategy_declares_the_shape_of_its_splits():
    # The frontend renders holdout controls or fold controls from this rather
    # than from the strategy's class name, which it used to compare against.
    assert ForecastingHoldoutEvaluationStrategy.get_metadata()["kind"] == "holdout"
    assert HoldoutEvaluationStrategy.get_metadata()["kind"] == "holdout"
    assert ForecastingCrossValidationEvaluationStrategy.get_metadata()["kind"] == "cv"
    assert CrossValidationEvaluationStrategy.get_metadata()["kind"] == "cv"


# --- which partitions get scored ---------------------------------------------


@pytest.mark.parametrize("strategy", FORECASTING_STRATEGIES)
def test_forecasting_strategies_do_not_score_the_training_partition(strategy):
    assert SplitEnum.TRAIN not in strategy.SCORED_SPLITS


def test_the_holdout_strategy_scores_validation_and_test():
    assert ForecastingHoldoutEvaluationStrategy.SCORED_SPLITS == (
        SplitEnum.VALIDATION,
        SplitEnum.TEST,
    )


def test_the_ordinary_holdout_strategy_still_scores_all_three():
    assert HoldoutEvaluationStrategy.SCORED_SPLITS == (
        SplitEnum.TRAIN,
        SplitEnum.VALIDATION,
        SplitEnum.TEST,
    )


# --- the final fit -----------------------------------------------------------


def test_the_kept_model_stops_at_the_end_of_training():
    xs, ys, _ = _split()
    strategy = ForecastingHoldoutEvaluationStrategy.__new__(
        ForecastingHoldoutEvaluationStrategy
    )
    model = ExponentialSmoothing(seasonal="add", season_length=12)

    strategy._fit_final_model(model, xs, ys)

    last_train_date = pd.to_datetime(xs["train"].to_pandas().iloc[:, 0]).max()
    assert model._last_train_date == last_train_date


def test_the_kept_model_is_the_one_the_validation_metrics_describe():
    from DashAI.back.metrics.regression.mae import MAE

    xs, ys, _ = _split()
    strategy = ForecastingHoldoutEvaluationStrategy.__new__(
        ForecastingHoldoutEvaluationStrategy
    )

    scored = ExponentialSmoothing(seasonal="add", season_length=12)
    scored.train(xs["train"], ys["train"])

    kept = ExponentialSmoothing(seasonal="add", season_length=12)
    strategy._fit_final_model(kept, xs, ys)

    assert MAE.score(ys["validation"], kept.predict(xs["validation"])) == MAE.score(
        ys["validation"], scored.predict(xs["validation"])
    )


def test_a_session_without_validation_rows_still_fits():
    xs, ys, _ = _split()
    empty = xs["validation"].select(range(0))
    xs = {**xs, "validation": empty}
    ys = {**ys, "validation": ys["validation"].select(range(0))}
    strategy = ForecastingHoldoutEvaluationStrategy.__new__(
        ForecastingHoldoutEvaluationStrategy
    )
    model = ExponentialSmoothing(seasonal="add", season_length=12)

    strategy._fit_final_model(model, xs, ys)

    last_train_date = pd.to_datetime(xs["train"].to_pandas().iloc[:, 0]).max()
    assert model._last_train_date == last_train_date


# --- hyperparameter trials ---------------------------------------------------


class _RecordingModel:
    """Stands in for a model, noting which partitions it is asked to score."""

    def __init__(self):
        self.scored = []

    def train(self, *args, **kwargs):
        return self

    def predict(self, x):
        import numpy as np

        return np.zeros(len(x))

    def prepare_output(self, y, is_fit=False):
        return y

    def calculate_metrics(self, split, level=None, **kwargs):
        self.scored.append(split)


def _evaluate_with(strategy_class):
    from DashAI.back.metrics.regression.mae import MAE

    xs, ys, _ = _split()
    strategy = strategy_class.__new__(strategy_class)
    model = _RecordingModel()
    strategy.evaluate(model, xs, ys, MAE)
    return model.scored


def test_a_forecasting_trial_never_scores_the_training_partition():
    scored = _evaluate_with(ForecastingHoldoutEvaluationStrategy)

    assert SplitEnum.TRAIN not in scored
    assert SplitEnum.VALIDATION in scored


def test_an_ordinary_trial_still_scores_both():
    scored = _evaluate_with(HoldoutEvaluationStrategy)

    assert SplitEnum.TRAIN in scored
    assert SplitEnum.VALIDATION in scored
