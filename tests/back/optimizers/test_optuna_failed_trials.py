"""A trial the model cannot fit must not take the whole study down with it.

Searching over the order of an ARIMA means asking statsmodels to fit
combinations that its state space cannot initialise, which surfaces as
``LinAlgError('LU decomposition error.')`` partway through the search. That is
a fact about the search space rather than a failure of the search: the trial
has no score, and the study should carry on and report the best of the ones
that did fit. Optuna re-raises whatever it is not told to catch, so a single
such trial used to end the run and the whole training job with it.

A programming error is a different thing and still stops the run, because
silently recording it as a failed trial would hide it behind a search that
merely looks unlucky.
"""

import numpy as np
import pytest

from DashAI.back.core.enums.metrics import LevelEnum, SplitEnum
from DashAI.back.optimizers.optuna_optimizer import OptunaOptimizer

BOUNDS = (0, 10)
N_TRIALS = 6


class DummyModel:
    """Minimal model whose score is just the value of its one parameter."""

    def __init__(self):
        self.p = 1

    def train(self, x, y, x_validation=None, y_validation=None):
        return self

    def predict(self, dataset):
        return self.p

    def calculate_metrics(self, split=None, level=None):
        assert split in (SplitEnum.TRAIN, SplitEnum.VALIDATION)
        assert level is LevelEnum.TRIAL

    def prepare_output(self, dataset, is_fit=False):
        return dataset


class DummyMetric:
    @staticmethod
    def score(y_true, y_pred):
        return y_pred


@pytest.fixture(name="dataset")
def dummy_dataset():
    return {"train": [0], "validation": [0]}


def _optimize(strategy, dataset, n_trials=N_TRIALS):
    """Run a study over one integer parameter with the given strategy."""
    model = DummyModel()
    optimizer = OptunaOptimizer(n_trials=n_trials, sampler="RandomSampler", pruner=None)
    optimizer.optimize(
        model,
        dataset,
        dataset,
        [(model, "p", BOUNDS, "integer")],
        {"class": DummyMetric, "metadata": {"maximize": True}},
        strategy,
    )
    return optimizer


def _strategy_failing(times, error):
    """Build a strategy that raises `error` for its first `times` calls."""
    calls = {"n": 0}

    def strategy(model, input_dataset, output_dataset, metric):
        calls["n"] += 1
        if calls["n"] <= times:
            raise error
        return metric.score(None, model.predict(input_dataset["validation"]))

    return strategy


def test_a_trial_the_model_cannot_fit_does_not_end_the_study(dataset):
    unfittable = _strategy_failing(2, np.linalg.LinAlgError("LU decomposition error."))

    optimizer = _optimize(unfittable, dataset)

    assert len(optimizer.get_trials_values()) == N_TRIALS - 2
    assert optimizer.get_best_params()["p"] in range(BOUNDS[0], BOUNDS[1] + 1)


def test_a_search_space_the_model_never_fits_says_so(dataset):
    never_fits = _strategy_failing(
        N_TRIALS, np.linalg.LinAlgError("LU decomposition error.")
    )

    with pytest.raises(ValueError, match="Every one of the") as raised:
        _optimize(never_fits, dataset)

    message = str(raised.value)
    assert "LU decomposition error." in message, (
        "the reason every trial failed has to reach the user, who is the only "
        "one who can narrow the search space"
    )
    assert "trial" in message.lower()


def test_a_programming_error_still_stops_the_study(dataset):
    broken = _strategy_failing(1, TypeError("predict() got an unexpected argument"))

    with pytest.raises(TypeError):
        _optimize(broken, dataset)
