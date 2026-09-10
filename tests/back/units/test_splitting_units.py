"""Contract tests for the two units that prepare a dataset and partition it.

Built on a hand-made ``ExecutionContext`` rather than through a job: the point
is what each unit reads, promises and refuses on its own, which a job that
always wires the context correctly cannot show.
"""

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
from DashAI.back.units.context import ExecutionContext, UnitContractError
from DashAI.back.units.prepare_and_fold_unit import PrepareAndFoldUnit
from DashAI.back.units.prepare_and_split_unit import PrepareAndSplitUnit

ROWS = 20


class SplitTask(BaseTask):
    name: str = "SplitTask"
    metadata: dict = {
        "inputs_types": [],
        "outputs_types": [],
        "inputs_cardinality": "n",
        "outputs_cardinality": 1,
    }

    def prepare_for_task(self, dataset, input_columns=None, output_columns=None):
        return dataset

    def num_labels(self, dataset, output_column):
        return 2


@pytest.fixture(name="registry")
def fixture_registry():
    registry = {
        "SplitTask": {"class": SplitTask},
        "HoldoutSplitter": {"class": HoldoutSplitter},
        "KFoldSplitter": {"class": KFoldSplitter},
    }
    di["component_registry"] = registry
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


def _split_unit(**splitter_params):
    params = {
        "train": 0.5,
        "test": 0.25,
        "validation": 0.25,
        "shuffle": True,
        "stratify": False,
        "random_state": 42,
    }
    params.update(splitter_params)
    return PrepareAndSplitUnit(
        task_name="SplitTask",
        input_columns=["a", "b"],
        output_columns=["y"],
        splitter={"component": "HoldoutSplitter", "params": params},
    )


def _fold_unit(**splitter_params):
    params = {
        "n_splits": 4,
        "test_size": 0.25,
        "shuffle": True,
        "random_state": 42,
    }
    params.update(splitter_params)
    return PrepareAndFoldUnit(
        task_name="SplitTask",
        input_columns=["a", "b"],
        output_columns=["y"],
        splitter={"component": "KFoldSplitter", "params": params},
    )


# --------------------------------------------------------------------------- #
# What each unit promises
# --------------------------------------------------------------------------- #


def test_the_holdout_unit_publishes_one_dataset_dict_per_side(registry):
    ctx = _context()

    _split_unit()(ctx)

    assert set(ctx.require("x")) == {"train", "test", "validation"}
    assert set(ctx.require("y")) == {"train", "test", "validation"}
    assert set(ctx.require("split_indexes")) == {
        "train_indexes",
        "test_indexes",
        "val_indexes",
    }


def test_the_fold_unit_publishes_a_list_and_not_the_holdout_keys(registry):
    """The reason the two are separate units and not one with a flag.

    Reusing ``x`` for a list would give one key two possible types, which a
    contract that compares key names cannot express.
    """
    ctx = _context()

    _fold_unit()(ctx)

    x_folds = ctx.require("x_folds")
    assert isinstance(x_folds, list)
    # Four folds plus the trailing entry, which is not a fold.
    assert len(x_folds) == 5
    assert not ctx.has("x")
    assert not ctx.has("y")


def test_every_fold_holds_a_train_and_a_validation_partition(registry):
    ctx = _context()

    _fold_unit()(ctx)

    x_folds = ctx.require("x_folds")
    for fold in x_folds[:-1]:
        assert set(fold) == {"train", "validation"}
    # The trailing entry fits the kept model and is scored on the reserved rows.
    assert set(x_folds[-1]) == {"train", "test"}


def test_the_fold_unit_keeps_the_reserved_rows_out_of_every_fold(registry):
    """Checked on the indexes the unit itself published."""
    ctx = _context()

    _fold_unit()(ctx)

    split_indexes = ctx.require("split_indexes")
    reserved = set(split_indexes["full_dataset"]["test_indexes"])
    assert reserved

    for name, partitions in split_indexes.items():
        if name == "full_dataset":
            continue
        seen = set(partitions["train_indexes"]) | set(partitions["validation_indexes"])
        assert reserved.isdisjoint(seen), name


def test_a_session_that_reserves_nothing_still_produces_folds(registry):
    ctx = _context()

    _fold_unit(test_size=0)(ctx)

    assert ctx.require("split_indexes")["full_dataset"]["test_indexes"] == []
    assert len(ctx.require("x_folds")) == 5


# --------------------------------------------------------------------------- #
# What the two share
# --------------------------------------------------------------------------- #


def test_the_two_units_prepare_the_dataset_the_same_way(registry):
    """Both run the same body, so the parts before the split cannot diverge.

    The one thing that differs is what the splitter returns, and everything
    upstream of it -- the task, the label count, the columns selected -- has to
    match or the two would be scoring different datasets.
    """
    holdout_ctx, fold_ctx = _context(), _context()

    _split_unit()(holdout_ctx)
    _fold_unit()(fold_ctx)

    assert holdout_ctx.require("n_labels") == fold_ctx.require("n_labels")
    assert holdout_ctx.require("task_name") == fold_ctx.require("task_name")
    assert type(holdout_ctx.require("task")) is type(fold_ctx.require("task"))

    holdout_columns = holdout_ctx.require("x")["train"].column_names
    fold_columns = fold_ctx.require("x_folds")[0]["train"].column_names
    assert holdout_columns == fold_columns == ["a", "b"]


@pytest.mark.parametrize("build", [_split_unit, _fold_unit])
def test_a_unit_refuses_to_run_before_a_dataset_was_loaded(registry, build):
    """``__call__`` checks REQUIRES, so the failure names the missing key."""
    with pytest.raises(UnitContractError):
        build()(ExecutionContext())


@pytest.mark.parametrize("build", [_split_unit, _fold_unit])
def test_an_unknown_task_is_reported_by_name(registry, build):
    unit = build()
    unit.config["task_name"] = "ThereIsNoSuchTask"

    with pytest.raises(JobError, match="Unable to find Task with name"):
        unit(_context())


@pytest.mark.parametrize("build", [_split_unit, _fold_unit])
def test_an_unknown_splitter_is_reported_by_name(registry, build):
    unit = build()
    unit.config["splitter"] = {"component": "ThereIsNoSuchSplitter", "params": {}}

    with pytest.raises(JobError, match="Unable to find Splitter with name"):
        unit(_context())


def test_the_splitters_own_refusal_is_passed_through_undecorated(registry):
    """More folds than rows is the splitter's diagnosis, not the unit's.

    It already names the numbers that explain the refusal, and a caller that
    wants to say which run this was frames it from outside. Decorating it here
    would push the numbers into the middle of someone else's sentence.
    """
    with pytest.raises(JobError) as error:
        _fold_unit(n_splits=ROWS + 1, test_size=0)(_context())

    message = " ".join(str(error.value).split())
    assert message == (
        f"Number of splits (n_splits={ROWS + 1}) cannot be greater "
        f"than the number of samples ({ROWS})."
    )


def test_two_units_in_one_context_do_not_share_their_resolved_task(registry):
    """Instance state stays on the instance, which is what lets a graph hold two.

    A context-global cache would give the second unit the first one's task,
    and the failure would be silent: the wrong task prepares the dataset
    without complaining.
    """
    first, second = _split_unit(), _fold_unit()
    ctx = _context()

    first(ctx)
    second(ctx)

    assert first._task is not None
    assert second._task is not None
    assert first._task is not second._task
