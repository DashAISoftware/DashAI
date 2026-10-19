"""Contract tests for the unit that prepares a dataset for a task with no target.

Built on a hand-made ``ExecutionContext`` rather than through a job, so what the
unit reads, promises and refuses is visible on its own. The scaling tests moved
here from ``tests/back/job_queue/test_model_job_clustering.py`` when the scaling
moved from ``ModelJob`` into this unit; that the job actually asks for it is
pinned end to end by the clustering regression net, which checks the stored
metrics against the scaled features.
"""

import numpy as np
import pandas as pd
import pytest
from kink import di

from DashAI.back.dataloaders.classes.dashai_dataset import (
    to_dashai_dataset,
    transform_dataset_with_schema,
)
from DashAI.back.job.base_job import JobError
from DashAI.back.models.scikit_learn.dbscan_clustering import DBSCANClustering
from DashAI.back.tasks.clustering_task import ClusteringTask
from DashAI.back.units.context import ExecutionContext, UnitContractError
from DashAI.back.units.prepare_without_target_unit import (
    PrepareWithoutTargetUnit,
    standardise_features,
)

ROWS = 60


@pytest.fixture(name="registry", autouse=True)
def fixture_registry():
    registry = {"ClusteringTask": {"class": ClusteringTask}}
    di["component_registry"] = registry
    yield registry
    del di["component_registry"]


def _mixed_scales(rows=ROWS, seed=0, extra=None):
    """Columns whose units are as far apart as a real tabular dataset's.

    ``score`` spans sixty units while ``hours`` spans ten, which is enough for
    the wider column to dominate every distance the models measure.
    """
    rng = np.random.default_rng(seed)
    frame = pd.DataFrame(
        {
            "hours": rng.uniform(1.0, 11.0, rows),
            "score": rng.uniform(40.0, 100.0, rows),
            "constant": np.ones(rows),
        }
    )
    schema = {name: {"type": "Float", "dtype": "float64"} for name in frame.columns}
    if extra:
        for name, (values, kind) in extra.items():
            frame[name] = values
            schema[name] = kind
    # Spelled out rather than inferred: a dataset built without a schema
    # carries no DashAI types, and the task refuses to prepare one.
    return transform_dataset_with_schema(to_dashai_dataset(frame), schema)


def _context(dataset=None):
    ctx = ExecutionContext()
    ctx.put("dataset", dataset if dataset is not None else _mixed_scales())
    ctx.put_ref("dataset_id", 7)
    return ctx


def _unit(**config):
    return PrepareWithoutTargetUnit(
        **{
            "task_name": "ClusteringTask",
            "input_columns": ["hours", "score", "constant"],
            "standardise": True,
            **config,
        }
    )


# --------------------------------------------------------------------------- #
# What the unit promises
# --------------------------------------------------------------------------- #


def test_the_unit_publishes_the_features_of_every_row():
    ctx = _context()

    _unit()(ctx)

    features = ctx.require("features").to_pandas()
    assert list(features.columns) == ["hours", "score", "constant"]
    assert len(features) == ROWS


def test_only_the_input_columns_reach_the_features():
    ctx = _context()

    _unit(input_columns=["score", "hours"])(ctx)

    assert set(ctx.require("features").column_names) == {"score", "hours"}


def test_a_task_without_a_target_has_no_label_count():
    ctx = _context()

    _unit()(ctx)

    assert ctx.require("n_labels") is None
    assert ctx.require("task_name") == "ClusteringTask"


def test_nothing_is_partitioned():
    """There is nothing to hold out, so none of the partition keys exist."""
    ctx = _context()

    _unit()(ctx)

    for key in ("x", "y", "x_folds", "y_folds", "split_indexes"):
        assert not ctx.has(key), key


# --------------------------------------------------------------------------- #
# The features the models are handed
# --------------------------------------------------------------------------- #


def test_every_numeric_column_is_centred_and_scaled():
    ctx = _context()

    _unit()(ctx)

    scaled = ctx.require("features").to_pandas()
    for column in ("hours", "score"):
        assert scaled[column].mean() == pytest.approx(0.0, abs=1e-12)
        assert scaled[column].std(ddof=0) == pytest.approx(1.0)


def test_a_column_without_variance_is_left_where_it_is():
    """Dividing it by a zero standard deviation is what produces the NaNs the
    models then refuse, so it is skipped rather than scaled."""
    ctx = _context()

    _unit()(ctx)

    assert (ctx.require("features").to_pandas()["constant"] == 1.0).all()


def test_the_features_are_left_raw_when_standardising_is_off():
    ctx = _context()
    raw = _mixed_scales().to_pandas()

    _unit(standardise=False)(ctx)

    pd.testing.assert_frame_equal(
        ctx.require("features").to_pandas(), raw, check_dtype=False
    )


def test_a_dataset_with_nothing_to_scale_is_returned_unchanged():
    x = to_dashai_dataset(pd.DataFrame({"constant": np.ones(5)}))

    assert standardise_features(x) is x


def test_the_row_and_column_shape_survives_scaling():
    x = _mixed_scales()

    scaled = standardise_features(x)

    assert scaled.to_pandas().shape == x.to_pandas().shape
    assert list(scaled.to_pandas().columns) == list(x.to_pandas().columns)


def test_scaling_is_what_lets_dbscan_find_anything_on_mixed_units():
    """The failure this guards against: with raw columns the default eps is far
    smaller than the spread of the widest one, so every row comes back noise."""
    x = _mixed_scales()

    raw = np.asarray(DBSCANClustering().train(x).get_cluster_labels(x))
    scaled_x = standardise_features(x)
    scaled = np.asarray(DBSCANClustering().train(scaled_x).get_cluster_labels(scaled_x))

    assert (raw == -1).all()
    assert (scaled != -1).any()


# --------------------------------------------------------------------------- #
# What the unit refuses
# --------------------------------------------------------------------------- #


def test_a_column_the_task_cannot_take_is_a_preparation_error():
    dataset = _mixed_scales(
        extra={
            "group": (
                ["a", "b", "c"] * (ROWS // 3),
                {"type": "Categorical", "dtype": "string"},
            )
        }
    )
    ctx = _context(dataset)

    with pytest.raises(JobError) as raised:
        _unit(input_columns=["hours", "group"])(ctx)

    assert str(raised.value) == "Can not prepare Dataset 7 for Task ClusteringTask"


def test_an_unknown_task_is_reported_by_name():
    ctx = _context()

    with pytest.raises(JobError) as raised:
        _unit(task_name="NoSuchTask")(ctx)

    assert str(raised.value) == "Unable to find Task with name NoSuchTask in registry"


@pytest.mark.parametrize("missing", ["dataset", "dataset_id"])
def test_the_unit_refuses_to_run_before_the_dataset_is_loaded(missing):
    """Absent is not the same as empty: a missing key is a wiring error."""
    ctx = ExecutionContext()
    if missing != "dataset":
        ctx.put("dataset", _mixed_scales())
    if missing != "dataset_id":
        ctx.put_ref("dataset_id", 7)

    with pytest.raises(UnitContractError):
        _unit()(ctx)


def test_two_units_do_not_share_a_resolved_task():
    first, second = _unit(), _unit()

    first(_context())
    second(_context())

    assert first._task is not second._task
