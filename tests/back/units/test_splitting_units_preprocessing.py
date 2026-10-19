"""What the two prepare units do with a session's fitted preprocessing.

Built on a hand-made ``ExecutionContext`` and on pickled stand-ins for the
``SessionPreprocessor`` that ``PreprocessingJob`` persists. The end-to-end net
in ``tests/back/api/test_model_job_preprocessing.py`` runs a real converter
through a real run; what it cannot show is *which* fit transformed each entry
and that the unit, not the preprocessor, is what narrows the columns.
"""

import pickle

import pandas as pd
import pyarrow as pa
import pytest
from kink import di

from DashAI.back.dataloaders.classes.dashai_dataset import to_dashai_dataset
from DashAI.back.job.base_job import JobError
from DashAI.back.splitters.holdout import HoldoutSplitter
from DashAI.back.splitters.k_fold import KFoldSplitter
from DashAI.back.tasks.base_task import BaseTask
from DashAI.back.types.value_types import Float
from DashAI.back.units.context import ExecutionContext
from DashAI.back.units.prepare_and_fold_unit import PrepareAndFoldUnit
from DashAI.back.units.prepare_and_split_unit import PrepareAndSplitUnit

ROWS = 20

#: One raw input and one converter-produced group, in that order.
REFS = [{"kind": "raw", "name": "b"}, {"kind": "group", "step": 0}]

HOLDOUT = {
    "train": 0.5,
    "test": 0.25,
    "validation": 0.25,
    "shuffle": True,
    "stratify": False,
    "random_state": 42,
}

K_FOLD = {"n_splits": 4, "test_size": 0.25, "shuffle": True, "random_state": 42}


class RecordingTask(BaseTask):
    """Records which input columns it was asked to validate."""

    name: str = "RecordingTask"
    metadata: dict = {
        "inputs_types": [],
        "outputs_types": [],
        "inputs_cardinality": "n",
        "outputs_cardinality": 1,
    }

    #: Shared by every instance: the unit builds its own task, so a test has
    #: no handle on the instance that was asked.
    asked_for = []

    def prepare_for_task(self, dataset, input_columns=None, output_columns=None):
        RecordingTask.asked_for.append(list(input_columns))
        return dataset

    def num_labels(self, dataset, output_column):
        return 2


class StampingPreprocessor:
    """Stands in for a fitted ``SessionPreprocessor``.

    Produces one column named after the artifact it was pickled under, so a
    test can read off each entry which fit transformed it. The column is
    computed from ``a``, a raw column that is not among the refs: the entry
    handed over has to still carry it, which is the reason ``x`` leaves the
    split un-narrowed. Nothing is dropped here, so the narrowing to the
    resolved inputs is the unit's doing and not this one's.
    """

    def __init__(self, name):
        self.produced = f"from_{name}"
        self.resolved_columns = {0: [self.produced]}
        self.resolved_slots = {0: {"Float": [self.produced]}}

    def transform_only(self, split):
        return {name: self._stamp(dataset) for name, dataset in split.items()}

    def _stamp(self, dataset):
        frame = dataset.to_pandas()
        frame[self.produced] = frame["a"] * 2.0
        types = dict(dataset.types)
        types[self.produced] = Float(arrow_type=pa.float64())
        return to_dashai_dataset(frame, types=types)


@pytest.fixture(name="registry")
def fixture_registry():
    registry = {
        "RecordingTask": {"class": RecordingTask},
        "HoldoutSplitter": {"class": HoldoutSplitter},
        "KFoldSplitter": {"class": KFoldSplitter},
    }
    di["component_registry"] = registry
    RecordingTask.asked_for.clear()
    yield registry
    del di["component_registry"]


def _dataset():
    frame = pd.DataFrame(
        {
            "a": [float(i) for i in range(ROWS)],
            "b": [float(i % 3) for i in range(ROWS)],
            "y": [float(i % 2) for i in range(ROWS)],
        }
    )
    types = {name: Float(arrow_type=pa.float64()) for name in frame.columns}
    return to_dashai_dataset(frame, types=types)


def _context():
    ctx = ExecutionContext()
    ctx.put("dataset", _dataset())
    ctx.put_ref("dataset_id", 7)
    return ctx


def _artifacts(directory, names):
    """Pickle one stand-in per name, the way PreprocessingJob lays them out."""
    for name in names:
        with open(directory / f"{name}.pkl", "wb") as file:
            pickle.dump(StampingPreprocessor(name), file)
    return str(directory)


def _split_unit(**config):
    return PrepareAndSplitUnit(
        task_name="RecordingTask",
        input_columns=["a", "b"],
        output_columns=["y"],
        splitter={"component": "HoldoutSplitter", "params": HOLDOUT},
        **config,
    )


def _fold_unit(**config):
    return PrepareAndFoldUnit(
        task_name="RecordingTask",
        input_columns=["a", "b"],
        output_columns=["y"],
        splitter={"component": "KFoldSplitter", "params": K_FOLD},
        **config,
    )


# --------------------------------------------------------------------------- #
# Which fit transforms which entry
# --------------------------------------------------------------------------- #


def test_the_holdout_unit_transforms_its_one_entry_with_the_final_fit(
    registry, tmp_path
):
    ctx = _context()
    unit = _split_unit(
        input_column_refs=REFS,
        preprocessing_artifacts_path=_artifacts(tmp_path, ["final"]),
    )

    unit(ctx)

    x = ctx.require("x")
    assert set(x) == {"train", "test", "validation"}
    for partition in x.values():
        # Narrowed to what the refs resolve to, in the order they are listed.
        assert partition.column_names == ["b", "from_final"]


def test_each_fold_is_transformed_with_its_own_fit(registry, tmp_path):
    """The leakage guarantee: fold i never sees a fit made on its own rows.

    Four folds and the trailing entry, each with a fit of its own; the
    stamp column carries the name of the artifact that was loaded for it.
    """
    ctx = _context()
    names = [f"fold_{i}" for i in range(4)] + ["final"]
    unit = _fold_unit(
        input_column_refs=REFS,
        preprocessing_artifacts_path=_artifacts(tmp_path, names),
    )

    unit(ctx)

    x_folds = ctx.require("x_folds")
    assert len(x_folds) == 5
    for fold, name in zip(x_folds, names, strict=True):
        for partition in fold.values():
            assert partition.column_names == ["b", f"from_{name}"], name


# --------------------------------------------------------------------------- #
# What reaches the task and the converters
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    ("build", "names"),
    [
        (_split_unit, ["final"]),
        (_fold_unit, [f"fold_{i}" for i in range(4)] + ["final"]),
    ],
    ids=["holdout", "folds"],
)
def test_the_task_validates_the_raw_refs_and_not_the_input_columns(
    registry, tmp_path, build, names
):
    """A group ref names a column that does not exist before the converter runs.

    So the task is validated on the raw refs alone, and ``input_columns``,
    which the job rewrites with the resolved names, plays no part.
    """
    unit = build(
        input_column_refs=REFS,
        preprocessing_artifacts_path=_artifacts(tmp_path, names),
    )

    unit(_context())

    assert RecordingTask.asked_for == [["b"]]


def test_the_converters_can_read_a_raw_column_that_is_not_a_final_input(
    registry, tmp_path
):
    """The reason the split carries every raw column and not only the inputs.

    The stand-in computes its column from ``a``, which the refs never name.
    Had ``x`` been narrowed before the split, the converter would have had
    nothing to read; the value it produced is the proof it did.
    """
    ctx = _context()
    unit = _split_unit(
        input_column_refs=REFS,
        preprocessing_artifacts_path=_artifacts(tmp_path, ["final"]),
    )

    unit(ctx)

    train = ctx.require("x")["train"].to_pandas()
    rows = ctx.require("split_indexes")["train_indexes"]
    # As a multiset: which rows the partition holds is the splitter's
    # answer, and in what order is not what this test is about.
    assert sorted(train["from_final"]) == sorted(float(i) * 2.0 for i in rows)


def test_the_output_side_is_untouched(registry, tmp_path):
    """An output ref is always raw, so ``y`` needs no transform and gets none."""
    ctx = _context()
    unit = _split_unit(
        input_column_refs=REFS,
        preprocessing_artifacts_path=_artifacts(tmp_path, ["final"]),
    )

    unit(ctx)

    y = ctx.require("y")
    for partition in y.values():
        assert partition.column_names == ["y"]
    assert ctx.require("n_labels") == 2


def test_without_preprocessing_the_input_columns_are_what_the_model_reads(
    registry,
):
    """The unit given neither param behaves as it always did."""
    ctx = _context()

    _split_unit()(ctx)

    assert RecordingTask.asked_for == [["a", "b"]]
    for partition in ctx.require("x").values():
        assert partition.column_names == ["a", "b"]


# --------------------------------------------------------------------------- #
# What the units refuse
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("build", [_split_unit, _fold_unit])
@pytest.mark.parametrize(
    "half",
    [
        {"input_column_refs": REFS},
        {"preprocessing_artifacts_path": "somewhere"},
    ],
    ids=["refs-only", "path-only"],
)
def test_one_runtime_param_without_the_other_is_a_wiring_mistake(registry, build, half):
    """Refs only resolve against a fit, and a fit without refs feeds nothing.

    Reading a half-configured unit as "no preprocessing" would train on raw
    columns and say nothing, which is the silent failure this exists to stop.
    """
    with pytest.raises(JobError, match="come together"):
        build(**half)(_context())


def test_a_missing_artifact_is_reported_by_name(registry, tmp_path):
    """The message names the entry, so a job can say which fit is missing."""
    unit = _fold_unit(
        input_column_refs=REFS,
        # fold_2 is not there.
        preprocessing_artifacts_path=_artifacts(
            tmp_path, ["fold_0", "fold_1", "fold_3", "final"]
        ),
    )

    with pytest.raises(JobError, match="fitted for fold_2"):
        unit(_context())


def test_malformed_refs_are_refused_before_anything_is_loaded(registry, tmp_path):
    unit = _split_unit(
        input_column_refs=[{"kind": "group"}],
        preprocessing_artifacts_path=_artifacts(tmp_path, ["final"]),
    )

    with pytest.raises(JobError, match="Can not parse input column refs"):
        unit(_context())
