"""Contract tests for the unit that fits a model on features alone.

Built on a hand-made ``ExecutionContext`` rather than through a job, so what the
unit reads, promises and refuses is visible on its own.
"""

import numpy as np
import pandas as pd
import pytest

from DashAI.back.dataloaders.classes.dashai_dataset import to_dashai_dataset
from DashAI.back.job.base_job import JobError
from DashAI.back.models.scikit_learn.kmeans_clustering import KMeansClustering
from DashAI.back.units.context import ExecutionContext, UnitContractError
from DashAI.back.units.fit_without_target_unit import FitWithoutTargetUnit


def _blobs(per_centre=30, seed=0):
    rng = np.random.default_rng(seed)
    points = np.vstack(
        [
            rng.normal(loc=c, scale=0.1, size=(per_centre, 2))
            for c in [(0.0, 0.0), (10.0, 10.0)]
        ]
    )
    return to_dashai_dataset(pd.DataFrame({"x": points[:, 0], "y": points[:, 1]}))


def _context(model, features=None):
    ctx = ExecutionContext()
    ctx.put("model", model)
    ctx.put("features", features if features is not None else _blobs())
    return ctx


def test_the_unit_fits_the_model_on_every_row():
    model = KMeansClustering(n_clusters=2, random_state=0)
    ctx = _context(model)

    FitWithoutTargetUnit()(ctx)

    labels = np.asarray(ctx.require("model").get_cluster_labels())
    assert labels.shape == (60,)
    assert set(labels[:30]) != set(labels[30:])


def test_the_fitted_model_is_the_one_that_came_in():
    """The scoring and saving units read the object that was trained, not a
    rebuilt one: asserted with ``is``, since equality would not show it."""
    model = KMeansClustering(n_clusters=2, random_state=0)
    ctx = _context(model)

    FitWithoutTargetUnit()(ctx)

    assert ctx.require("model") is model


def test_a_model_that_needs_a_target_is_refused_before_fitting():
    class _Supervised:
        trained = False

        def train(self, *args):
            self.trained = True

    model = _Supervised()
    ctx = _context(model)

    with pytest.raises(JobError) as raised:
        FitWithoutTargetUnit()(ctx)

    assert str(raised.value) == (
        "_Supervised cannot be trained without a target: only clustering models can."
    )
    assert model.trained is False


def test_a_failing_fit_is_reported_with_its_reason(monkeypatch):
    def fail(self, *args, **kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr(KMeansClustering, "train", fail)
    ctx = _context(KMeansClustering(n_clusters=2))

    with pytest.raises(JobError) as raised:
        FitWithoutTargetUnit()(ctx)

    assert str(raised.value) == "Model training failed boom"


@pytest.mark.parametrize("missing", ["model", "features"])
def test_the_unit_refuses_to_run_without_its_inputs(missing):
    """Absent is not the same as empty: a missing key is a wiring error."""
    ctx = ExecutionContext()
    if missing != "model":
        ctx.put("model", KMeansClustering(n_clusters=2))
    if missing != "features":
        ctx.put("features", _blobs())

    with pytest.raises(UnitContractError):
        FitWithoutTargetUnit()(ctx)
