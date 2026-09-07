"""Which tasks each optimizer is offered for.

Adding a task does not by itself make the components that gate on tasks aware
of it. Forecasting was registered with models, metrics and splitters but not
with any optimizer, so the optimizer dropdown came up empty and hyperparameter
search was unreachable for it.
"""

from DashAI.back.optimizers.optuna_optimizer import OptunaOptimizer


def test_optuna_serves_forecasting():
    # ARIMA's p, d and q, and the season lengths on the other models, are all
    # declared as optimizable, so there is something for it to search.
    assert "ForecastingTask" in OptunaOptimizer.COMPATIBLE_COMPONENTS


def test_optuna_keeps_serving_the_tasks_it_already_did():
    for task in (
        "TabularClassificationTask",
        "TextClassificationTask",
        "TranslationTask",
        "RegressionTask",
    ):
        assert task in OptunaOptimizer.COMPATIBLE_COMPONENTS


def test_every_forecasting_model_declares_something_to_optimize():
    # An optimizer with nothing to search would be a pointless offer.
    from DashAI.back.models.forecasting.arima import ARIMA
    from DashAI.back.models.forecasting.exponential_smoothing import (
        ExponentialSmoothing,
    )
    from DashAI.back.models.forecasting.seasonal_naive import SeasonalNaiveForecaster

    for model in (ARIMA, SeasonalNaiveForecaster, ExponentialSmoothing):
        fields = model.SCHEMA.model_json_schema()["properties"]
        optimizable = [
            name
            for name, spec in fields.items()
            if "optimize" in str(spec.get("placeholder", ""))
        ]
        assert optimizable, f"{model.__name__} has no optimizable field"
