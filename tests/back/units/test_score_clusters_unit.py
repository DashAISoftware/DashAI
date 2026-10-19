"""Contract tests for the unit that scores a fitted clustering.

Built on a hand-made ``ExecutionContext`` rather than through a job, so what the
unit reads, promises and refuses is visible on its own. The degenerate cases
moved here from ``tests/back/job_queue/test_model_job_clustering.py`` when the
guard moved from ``ModelJob`` into this unit.
"""

import math

import numpy as np
import pandas as pd
import pytest
from kink import di

from DashAI.back.dataloaders.classes.dashai_dataset import (
    to_dashai_dataset,
    transform_dataset_with_schema,
)
from DashAI.back.job.base_job import JobError
from DashAI.back.metrics.clustering.calinski_harabasz import CalinskiHarabasz
from DashAI.back.metrics.clustering.davies_bouldin import DaviesBouldin
from DashAI.back.metrics.clustering.silhouette import Silhouette
from DashAI.back.models.scikit_learn.dbscan_clustering import DBSCANClustering
from DashAI.back.models.scikit_learn.kmeans_clustering import KMeansClustering
from DashAI.back.units.context import ExecutionContext, UnitContractError
from DashAI.back.units.score_clusters_unit import ScoreClustersUnit

METRICS = [Silhouette, CalinskiHarabasz, DaviesBouldin]
NAMES = [metric.__name__ for metric in METRICS]
DEGENERATE_TAIL = (
    "Clustering metrics need at least two clusters, so this run has no result "
    "to report. Adjust the model parameters, for instance a larger eps or a "
    "smaller min_samples for DBSCAN."
)


class _Answers:
    """A metric whose score is whatever the test says."""

    MAXIMIZE = True

    def __init_subclass__(cls, value=None, **kwargs):
        super().__init_subclass__(**kwargs)
        cls.value = value

    @classmethod
    def score(cls, x, labels):
        return cls.value


class NotANumber(_Answers, value=float("nan")):
    pass


class Infinite(_Answers, value=float("inf")):
    pass


class Undefined(_Answers, value=None):
    pass


class Finite(_Answers, value=0.25):
    pass


@pytest.fixture(name="registry", autouse=True)
def fixture_registry():
    registry = {
        metric.__name__: {"class": metric}
        for metric in [*METRICS, NotANumber, Infinite, Undefined, Finite]
    }
    di["component_registry"] = registry
    yield registry
    del di["component_registry"]


def _blobs(per_centre=30, seed=0):
    rng = np.random.default_rng(seed)
    points = np.vstack(
        [
            rng.normal(loc=c, scale=0.1, size=(per_centre, 2))
            for c in [(0.0, 0.0), (10.0, 10.0)]
        ]
    )
    return transform_dataset_with_schema(
        to_dashai_dataset(pd.DataFrame({"x": points[:, 0], "y": points[:, 1]})),
        {name: {"type": "Float", "dtype": "float64"} for name in ("x", "y")},
    )


def _fitted(model, features):
    model.train(features)
    ctx = ExecutionContext()
    ctx.put("model", model)
    ctx.put("features", features)
    return ctx


def _kmeans_context():
    return _fitted(KMeansClustering(n_clusters=2, random_state=0), _blobs())


# --------------------------------------------------------------------------- #
# What the unit promises
# --------------------------------------------------------------------------- #


def test_the_scores_are_published_for_the_full_dataset():
    ctx = _kmeans_context()

    ScoreClustersUnit(metrics=NAMES)(ctx)

    features = ctx.require("features")
    labels = ctx.require("model").get_cluster_labels(features)
    expected = {metric.__name__: metric.score(features, labels) for metric in METRICS}
    assert ctx.require("metrics") == {"full": pytest.approx(expected)}


def test_only_the_requested_metrics_are_scored():
    ctx = _kmeans_context()

    ScoreClustersUnit(metrics=["Silhouette"])(ctx)

    assert set(ctx.require("metrics")["full"]) == {"Silhouette"}


def test_the_scores_are_a_reference_that_survives_leaving_the_process():
    ctx = _kmeans_context()

    ScoreClustersUnit(metrics=NAMES)(ctx)

    assert ctx.origin("metrics") == "ref"


# --------------------------------------------------------------------------- #
# Scores that are not numbers
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("metric", [NotANumber, Infinite])
def test_a_non_finite_score_is_left_out(metric):
    """The rule ``BaseModel._score_split`` applies to supervised scores: a NaN
    that reaches a comparison poisons every one downstream of it."""
    ctx = _kmeans_context()

    ScoreClustersUnit(metrics=[metric.__name__, "Finite"])(ctx)

    assert ctx.require("metrics") == {"full": {"Finite": 0.25}}
    assert all(math.isfinite(v) for v in ctx.require("metrics")["full"].values())


def test_an_undefined_score_is_left_out():
    ctx = _kmeans_context()

    ScoreClustersUnit(metrics=["Undefined", "Finite"])(ctx)

    assert ctx.require("metrics") == {"full": {"Finite": 0.25}}


def test_every_score_left_out_is_an_empty_result_not_a_failure():
    ctx = _kmeans_context()

    ScoreClustersUnit(metrics=["NotANumber", "Undefined"])(ctx)

    assert ctx.require("metrics") == {"full": {}}


# --------------------------------------------------------------------------- #
# The three failures, each with its own text
# --------------------------------------------------------------------------- #


def test_labels_that_cannot_be_read_are_a_training_failure(monkeypatch):
    """To the user the labels are what training produced."""

    def fail(self, x=None):
        raise RuntimeError("boom")

    ctx = _kmeans_context()
    monkeypatch.setattr(KMeansClustering, "get_cluster_labels", fail)

    with pytest.raises(JobError) as raised:
        ScoreClustersUnit(metrics=NAMES)(ctx)

    assert str(raised.value) == "Model training failed boom"
    assert not ctx.has("metrics")


def test_a_run_where_every_point_is_noise_has_nothing_to_score():
    ctx = _fitted(DBSCANClustering(eps=0.5, min_samples=1000), _blobs())

    with pytest.raises(JobError) as raised:
        ScoreClustersUnit(metrics=NAMES)(ctx)

    assert str(raised.value) == (
        "DBSCANClustering produced 0 cluster(s) over 60 samples, 60 of them "
        "labelled as noise. " + DEGENERATE_TAIL
    )
    assert not ctx.has("metrics")


def test_a_single_cluster_has_nothing_to_score():
    ctx = _fitted(KMeansClustering(n_clusters=1, random_state=0), _blobs())

    with pytest.raises(JobError) as raised:
        ScoreClustersUnit(metrics=NAMES)(ctx)

    assert str(raised.value) == (
        "KMeansClustering produced 1 cluster(s) over 60 samples, 0 of them "
        "labelled as noise. " + DEGENERATE_TAIL
    )


def test_a_metric_that_raises_is_a_metric_failure(monkeypatch):
    def fail(x, labels):
        raise RuntimeError("boom")

    ctx = _kmeans_context()
    monkeypatch.setattr(Silhouette, "score", staticmethod(fail))

    with pytest.raises(JobError) as raised:
        ScoreClustersUnit(metrics=NAMES)(ctx)

    assert str(raised.value) == "Metric calculation failed boom"
    assert not ctx.has("metrics")


def test_an_unknown_metric_is_refused_before_scoring():
    """Refused by ``validate``, on an empty context: no labels are read and no
    model is needed, which is what "before scoring" means. Going through
    ``__call__`` would pass even if the lookup only happened in ``execute``."""
    with pytest.raises(JobError) as raised:
        ScoreClustersUnit(metrics=["NoSuchMetric"]).validate(ExecutionContext())

    assert (
        str(raised.value) == "Unable to find Metric with name NoSuchMetric in registry."
    )


@pytest.mark.parametrize("missing", ["model", "features"])
def test_the_unit_refuses_to_run_without_its_inputs(missing):
    """Absent is not the same as empty: a missing key is a wiring error."""
    full = _kmeans_context()
    ctx = ExecutionContext()
    for key in ("model", "features"):
        if key != missing:
            ctx.put(key, full.require(key))

    with pytest.raises(UnitContractError):
        ScoreClustersUnit(metrics=NAMES)(ctx)
