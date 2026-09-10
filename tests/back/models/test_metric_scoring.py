"""A non-finite score must not leave by one door and stay in through the other.

``calculate_metrics`` and ``compute_metrics`` used to carry a copy each of the
same scoring loop, and the copies drifted. Only the first dropped non-finite
scores: the second returned the NaN untouched, and that is the one the CV
evaluation loop calls to build the objective of an HPO trial. So a metric too
suspect to be written to the database was still comparable enough to decide
which hyperparameters won -- and every comparison against a NaN is False, so
the trial that produced it could never be beaten and could never win.

These tests pin the two methods to one loop by asserting they agree.
"""

import math

import pytest

from DashAI.back.core.enums.metrics import LevelEnum, SplitEnum
from DashAI.back.models.base_model import BaseModel


class _Metric:
    """The smallest thing the scoring loop accepts: a name and a score."""

    def __init__(self, name, value):
        self.__name__ = name
        self._value = value

    def score(self, y_true, y_pred):
        return self._value


class _StubModel(BaseModel):
    """A model that predicts nothing, so only the scoring loop is under test."""

    def train(self, *args, **kwargs):
        return self

    def save(self, filename):  # pragma: no cover - not exercised here
        raise NotImplementedError

    def load(self, filename):  # pragma: no cover - not exercised here
        raise NotImplementedError

    def predict(self, x):
        return [0.0]

    def prepare_output(self, dataset, is_fit=False):
        return dataset


@pytest.fixture(name="model")
def fixture_model():
    model = _StubModel()
    model.run_id = 1
    model.x_data = None
    model.y_data = None
    model.train_metrics = None
    model.test_metrics = None
    model.validation_metrics = None
    return model


@pytest.mark.parametrize("bad", [float("nan"), float("inf"), float("-inf")])
def test_compute_metrics_drops_non_finite_scores(model, bad):
    """The value that must never reach an objective must never be returned.

    Before the shared loop, ``compute_metrics`` returned ``{"good": 1.0,
    "bad": nan}``: the mean of a fold's scores was then NaN, and NaN compares
    False against every other trial in both directions.
    """
    model.validation_metrics = [_Metric("good", 1.0), _Metric("bad", bad)]

    scores = model.compute_metrics(split=SplitEnum.VALIDATION, x_data=[], y_data=[])

    assert scores == {"good": 1.0}, (
        f"a {bad} score survived into the mapping the HPO objective is built from"
    )
    assert all(math.isfinite(v) for v in scores.values())


def test_both_methods_agree_on_what_was_scored(model):
    """The two entry points must report the same set of metrics.

    This is the assertion that would have caught the drift: whatever the policy
    on non-finite scores is, the logged metrics and the optimized metrics have
    to be the same ones, or the run is tuned on numbers nobody can see.
    """
    model.validation_metrics = [_Metric("good", 1.0), _Metric("bad", float("nan"))]

    persisted = {}
    model._save_metrics = lambda **kwargs: persisted.update(kwargs["results"])

    model.calculate_metrics(
        split=SplitEnum.VALIDATION,
        level=LevelEnum.LAST,
        x_data=[],
        y_data=[],
    )
    returned = model.compute_metrics(split=SplitEnum.VALIDATION, x_data=[], y_data=[])

    assert persisted == returned


def test_no_metrics_declared_returns_an_empty_mapping(model):
    """A split with no metrics is not an error, and must not look like a score."""
    assert model.compute_metrics(split=SplitEnum.VALIDATION, x_data=[], y_data=[]) == {}


def test_every_metric_non_finite_is_not_the_same_as_no_metrics(model):
    """Both answer ``{}`` to the caller, but only one gets logged about.

    ``_score_split`` distinguishes them -- ``None`` for a question that could
    not be asked, an empty dict for one whose answers were all unusable -- and
    ``calculate_metrics`` relies on that to persist an empty result rather than
    skip the split silently.
    """
    model.validation_metrics = [_Metric("bad", float("nan"))]

    assert model._score_split(SplitEnum.VALIDATION, x_data=[], y_data=[]) == {}

    model.validation_metrics = None
    assert model._score_split(SplitEnum.VALIDATION, x_data=[], y_data=[]) is None
