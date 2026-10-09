import math

import numpy as np
import pandas as pd
import pytest

from DashAI.back.dataloaders.classes.dashai_dataset import to_dashai_dataset
from DashAI.back.metrics.forecasting.mape import MAPE
from DashAI.back.metrics.forecasting.smape import SMAPE
from DashAI.back.metrics.regression_metric import RegressionMetric


def _true(values):
    return to_dashai_dataset(pd.DataFrame({"target": values}))


def test_mape_matches_a_hand_computed_value():
    # errors 10/100 and 20/200 -> 10% and 10% -> 10%
    score = MAPE.score(_true([100.0, 200.0]), np.array([110.0, 180.0]))

    assert score == pytest.approx(10.0)


def test_mape_is_zero_for_a_perfect_forecast():
    assert MAPE.score(_true([1.0, 2.0]), np.array([1.0, 2.0])) == pytest.approx(0.0)


def test_mape_skips_zero_actuals_rather_than_dividing_by_them():
    # The zero row is undefined for MAPE, so it is left out; the remaining
    # row is off by 10 percent.
    score = MAPE.score(_true([0.0, 100.0]), np.array([5.0, 110.0]))

    assert score == pytest.approx(10.0)


def test_mape_is_not_a_number_when_every_actual_is_zero():
    score = MAPE.score(_true([0.0, 0.0]), np.array([1.0, 2.0]))

    assert math.isnan(score)


def test_smape_matches_a_hand_computed_value():
    # |100-110| = 10, denominator (100+110)/2 = 105 -> 2*10/210 = 9.5238%
    score = SMAPE.score(_true([100.0]), np.array([110.0]))

    assert score == pytest.approx(200 * 10 / 210)


def test_smape_is_zero_for_a_perfect_forecast():
    assert SMAPE.score(_true([1.0, 2.0]), np.array([1.0, 2.0])) == pytest.approx(0.0)


def test_smape_survives_a_zero_actual():
    # The case that breaks MAPE. Predicting 5 when the truth is 0 is the
    # worst possible relative error, which sMAPE caps at 200 percent.
    score = SMAPE.score(_true([0.0]), np.array([5.0]))

    assert score == pytest.approx(200.0)


def test_smape_treats_a_matching_pair_of_zeros_as_no_error():
    score = SMAPE.score(_true([0.0, 100.0]), np.array([0.0, 100.0]))

    assert score == pytest.approx(0.0)


def test_both_metrics_are_minimised():
    assert MAPE.MAXIMIZE is False
    assert SMAPE.MAXIMIZE is False


def test_both_metrics_serve_forecasting_and_regression():
    # Both routes to a forecast need them: the native task, and the windowed
    # data that goes through RegressionTask.
    for metric in (MAPE, SMAPE):
        assert issubclass(metric, RegressionMetric)


def test_regression_metrics_are_available_to_forecasting():
    assert "ForecastingTask" in RegressionMetric.COMPATIBLE_COMPONENTS
    assert "RegressionTask" in RegressionMetric.COMPATIBLE_COMPONENTS
