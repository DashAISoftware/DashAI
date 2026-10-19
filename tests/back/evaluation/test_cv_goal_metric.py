"""A fold whose objective is not a number must say so, not poison the mean.

``FitModelOverFoldsUnit._score_folds`` scores the goal metric on every fold and
returns the mean as the objective of an HPO trial. A metric can come back
non-finite on a fold, a classification metric on a fold with a single class,
say, and a NaN in the mean is worse than an error: NaN compares False against
every other trial in both directions, so the trial that produced it could never
be beaten and could never win.

Skipping the fold instead would be worse than either: the objective would then
be the mean of a different set of folds on each trial, and those means are not
comparable, so the study would rank trials by which folds happened to work.

This used to live in ``FoldEvaluationStrategy.evaluate``, which read the goal
metric out of ``compute_metrics`` and could therefore also find it missing. The
unit scores the goal metric directly, so the only way it can go missing is by
not being a number, and that is the case pinned here.
"""

import math

import pytest

from DashAI.back.units.fit_model_over_folds_unit import FitModelOverFoldsUnit


class R2:
    """The goal metric, as a class: the error names it by ``__name__``.

    Named rather than given a ``__name__`` attribute, because assigning one in
    a class body does not change what ``cls.__name__`` returns: ``type``
    defines it as a data descriptor, which wins over the class dict.
    """

    #: One value per fold, consumed in order.
    values = []

    @classmethod
    def score(cls, y_true, y_pred):
        return cls.values.pop(0)


class _StubModel:
    """A model whose only interesting behaviour is what it scores."""

    def __init__(self):
        self.x_data = None
        self.y_data = None

    def train(self, *args, **kwargs):
        return self

    def predict(self, x_data):
        return x_data

    def prepare_output(self, y_data, is_fit=False):
        return y_data

    def compute_metrics(self, split, x_data=None, y_data=None):
        return None

    def _save_metrics(self, **kwargs):  # pragma: no cover - never reached here
        raise AssertionError("an inner trial records nothing")


def _unit():
    return FitModelOverFoldsUnit(
        optimizer={"component": "AnOptimizer", "params": {}},
        goal_metric="R2",
        run_id=None,
        artifact_prefix="none",
    )


def _score(values):
    """Score two folds with the given goal metric values, recording nothing."""
    R2.values = list(values)
    #: Three entries make two folds: the last element is the pool, not a fold.
    folds = [
        {"train": "t0", "validation": "v0"},
        {"train": "t1", "validation": "v1"},
        {"train": "pool", "test": "reserved"},
    ]
    return _unit()._score_folds(_StubModel(), folds, folds, R2, record=False)


@pytest.mark.parametrize("bad", [float("nan"), float("inf"), float("-inf")])
def test_a_non_finite_goal_metric_names_itself(bad):
    """The error has to carry the metric asked for and the fold it failed on."""
    with pytest.raises(RuntimeError) as excinfo:
        _score([0.5, bad])

    message = str(excinfo.value)
    assert "R2" in message, "the error does not name the metric"
    assert "Fold 1" in message, "the error does not name the fold"


def test_it_is_not_a_valueerror():
    """``study.optimize`` catches ValueError, so this must not be one.

    ``OptunaOptimizer`` runs the study with ``catch=UNFITTABLE_TRIAL_ERRORS``,
    which includes ``ValueError``. Raising one here would be swallowed trial by
    trial and reported as "all N trials failed, narrow the ranges and try
    again", advice that has nothing to do with a metric that is undefined on
    the fold's data. The same reasoning is already written into the optimizer,
    where an unsupported parameter type raises ``TypeError`` for this exact
    reason.
    """
    from DashAI.back.optimizers.optuna_optimizer import UNFITTABLE_TRIAL_ERRORS

    with pytest.raises(RuntimeError) as excinfo:
        _score([float("nan"), 0.5])

    assert not isinstance(excinfo.value, UNFITTABLE_TRIAL_ERRORS), (
        "the optimizer would catch this and report it as an unfittable trial"
    )


def test_a_fold_with_a_finite_goal_metric_still_returns_the_mean():
    """The guard must not change the answer when there is nothing wrong."""
    objective = _score([0.5, 1.0])

    assert math.isfinite(objective)
    assert objective == pytest.approx(0.75)
