"""A fold that produced no objective must say so, not raise ``KeyError``.

``FoldEvaluationStrategy.evaluate`` indexed the fold's validation scores with
the goal metric's name and trusted it to be there. It is not always: the metric
may not be among the validation metrics selected for the run, and since
``compute_metrics`` drops non-finite scores it can also be missing because it
was undefined on that fold's data. Both are configuration problems, and both
surfaced as a bare ``KeyError`` with a metric name in it, several frames below
where the choice was made.

Skipping the fold instead would be worse than either: the objective would then
be the mean of a different set of folds on each trial, and those means are not
comparable, so the study would rank trials by which folds happened to work.
"""

import pytest

from DashAI.back.core.enums.metrics import SplitEnum
from DashAI.back.evaluation.cv import FoldEvaluationStrategy


class R2:
    """The goal metric, as a class: ``evaluate`` looks it up by ``__name__``.

    Named rather than given a ``__name__`` attribute, because assigning one in
    a class body does not change what ``cls.__name__`` returns -- ``type``
    defines it as a data descriptor, which wins over the class dict.
    """

    @staticmethod
    def score(y_true, y_pred):  # pragma: no cover - never reached here
        return 0.0


class _StubModel:
    """A model whose only interesting behaviour is what it scores."""

    def __init__(self, scores):
        self._scores = scores
        self.x_data = None
        self.y_data = None

    def train(self, *args, **kwargs):
        return self

    def compute_metrics(self, split=SplitEnum.TEST, **kwargs):
        return dict(self._scores)

    def _save_metrics(self, **kwargs):
        pass


def _strategy():
    """A strategy with no factory: only its class attributes are read here."""
    return FoldEvaluationStrategy.__new__(FoldEvaluationStrategy)


#: Two entries make one fold: the last element is the pool, not a fold.
FOLDS = [{"train": [], "validation": []}, {"train": [], "test": []}]


def test_a_missing_goal_metric_names_itself():
    """The error has to carry the metric asked for and the metrics obtained."""
    model = _StubModel({"MSE": 0.5, "MAE": 0.3})

    with pytest.raises(RuntimeError) as excinfo:
        _strategy().evaluate(model, FOLDS, FOLDS, R2)

    message = str(excinfo.value)
    assert "R2" in message, "the error does not name the metric that is missing"
    assert "MAE, MSE" in message, "the error does not name what was scored"


def test_it_is_not_a_valueerror():
    """``study.optimize`` catches ValueError, so this must not be one.

    ``OptunaOptimizer`` runs the study with ``catch=UNFITTABLE_TRIAL_ERRORS``,
    which includes ``ValueError``. Raising one here would be swallowed trial by
    trial and reported as "all N trials failed, narrow the ranges and try
    again" -- advice that has nothing to do with a metric that was never
    computed. The same reasoning is already written into the optimizer, where
    an unsupported parameter type raises ``TypeError`` for this exact reason.
    """
    from DashAI.back.optimizers.optuna_optimizer import UNFITTABLE_TRIAL_ERRORS

    model = _StubModel({"MSE": 0.5})

    with pytest.raises(RuntimeError) as excinfo:
        _strategy().evaluate(model, FOLDS, FOLDS, R2)

    assert not isinstance(excinfo.value, UNFITTABLE_TRIAL_ERRORS), (
        "the optimizer would catch this and report it as an unfittable trial"
    )


def test_a_fold_with_the_goal_metric_still_returns_its_mean():
    """The guard must not change the answer when there is nothing wrong."""
    model = _StubModel({"R2": 0.75})

    assert _strategy().evaluate(model, FOLDS, FOLDS, R2) == pytest.approx(0.75)
