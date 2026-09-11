"""Contract tests for the exploration units, isolated from any orchestrating job.

The context is built by hand rather than through a job, which is what exposes
composability mistakes: a job always wires the context "correctly", so an
end-to-end run cannot tell a real contract from a lucky one.
"""

import pathlib

import pytest
from kink import di

from DashAI.back.dataloaders.classes.dashai_dataset import to_dashai_dataset
from DashAI.back.exploration.base_explorer import BaseExplorer
from DashAI.back.job.base_job import JobError
from DashAI.back.units.context import ExecutionContext, UnitContractError
from DashAI.back.units.run_exploration_unit import RunExplorationUnit
from DashAI.back.units.save_exploration_unit import SaveExplorationUnit


class _ExplorerRow:
    """Stand-in for an Explorer ORM row."""

    def __init__(
        self, notebook_id=3, columns=None, exploration_type="RecordingExplorer"
    ):
        self.id = 11
        self.notebook_id = notebook_id
        self.columns = columns if columns is not None else [{"columnName": "a"}]
        self.exploration_type = exploration_type
        self.name = "an exploration"


class _NotebookRow:
    """Stand-in for a Notebook ORM row."""

    def __init__(self, notebook_id=3):
        self.id = notebook_id


class _FakeSession:
    def __init__(self, rows):
        self._rows = rows

    def get(self, model, row_id):
        return self._rows.get(model.__name__, {}).get(row_id)

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        return False


class _FakeSessionFactory:
    """Stand-in for a ``sessionmaker``.

    A class rather than a lambda on purpose: kink invokes any registered lambda
    with the container to resolve it, so a lambda here would be called as a
    service factory instead of being handed to the unit as one.
    """

    def __init__(self, rows):
        self._rows = rows

    def __call__(self):
        return _FakeSession(self._rows)


class RecordingExplorer(BaseExplorer):
    """Explorer that records what the units hand it, and when."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.marker = kwargs.get("marker")
        self.seen_columns = None
        self.seen_row_name = None

    def prepare_dataset(self, loaded_dataset, columns):
        self.seen_columns = [column["columnName"] for column in columns]
        return loaded_dataset.select_columns(self.seen_columns)

    def launch_exploration(self, dataset, explorer_info):
        self.seen_row_name = explorer_info.name
        return {"rows": len(dataset), "columns": dataset.column_names}

    def save_notebook(self, notebook_info, explorer_info, save_path, result):
        # Reads instance state set at construction time, the way CorrMatrix
        # reads self.plot, and returns a str the way DescribeExplorer does.
        target = pathlib.Path(save_path) / f"{explorer_info.id}-{self.marker}.txt"
        target.write_text(str(result), encoding="utf-8")
        return target.as_posix()

    def get_results(self, exploration_path, options):
        return []


class BadPathExplorer(RecordingExplorer):
    """Explorer whose save returns something that is not a path."""

    def save_notebook(self, notebook_info, explorer_info, save_path, result):
        return 42


class ExplodingExplorer(RecordingExplorer):
    def launch_exploration(self, dataset, explorer_info):
        raise RuntimeError("the exploration itself blew up")


@pytest.fixture(name="registry")
def fixture_registry():
    registry = {
        "RecordingExplorer": {"class": RecordingExplorer},
        "BadPathExplorer": {"class": BadPathExplorer},
        "ExplodingExplorer": {"class": ExplodingExplorer},
    }
    di["component_registry"] = registry
    yield registry
    del di["component_registry"]


@pytest.fixture(name="fake_db")
def fixture_fake_db():
    rows = {
        "Explorer": {11: _ExplorerRow()},
        "Notebook": {3: _NotebookRow()},
    }
    di["session_factory"] = _FakeSessionFactory(rows)
    yield rows
    del di["session_factory"]


@pytest.fixture(name="notebook_path")
def fixture_notebook_path(tmp_path):
    config = {"NOTEBOOK_PATH": tmp_path / "notebooks"}
    di["config"] = config
    yield config["NOTEBOOK_PATH"]
    del di["config"]


@pytest.fixture(name="ctx")
def fixture_ctx():
    """A context holding a three-column dataset, as a loader would leave it."""
    import pandas as pd
    import pyarrow as pa

    from DashAI.back.types.value_types import Integer

    frame = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6], "c": [7, 8, 9]})
    types = {name: Integer(arrow_type=pa.int64()) for name in ("a", "b", "c")}

    context = ExecutionContext()
    context.put("dataset", to_dashai_dataset(frame, types=types))
    return context


def _explorer(component="RecordingExplorer", **params):
    return {"component": component, "params": {"marker": "x", **params}}


# --- RunExplorationUnit -------------------------------------------------


def test_run_exploration_publishes_the_result_and_the_explorer(ctx, registry, fake_db):
    """Both outputs are declared, so both must be there.

    The explorer instance is an output and not a private detail: saving is a
    method on it, and the save unit has to receive the object that ran.
    """
    RunExplorationUnit(explorer_id=11, explorer=_explorer())(ctx)

    assert ctx.require("exploration_result") == {"rows": 3, "columns": ["a"]}
    assert isinstance(ctx.require("explorer"), RecordingExplorer)


def test_run_exploration_narrows_the_dataset_to_the_rows_selected_columns(
    ctx, registry, fake_db
):
    """The column list comes from the row, resolved against the dataset the
    context holds right now — never against a list captured earlier."""
    fake_db["Explorer"][11].columns = [{"columnName": "b"}, {"columnName": "c"}]

    RunExplorationUnit(explorer_id=11, explorer=_explorer())(ctx)

    assert ctx.require("explorer").seen_columns == ["b", "c"]


def test_run_exploration_hands_the_row_to_the_component(ctx, registry, fake_db):
    """``launch_exploration`` takes the ORM row; the unit re-reads it itself."""
    RunExplorationUnit(explorer_id=11, explorer=_explorer())(ctx)

    assert ctx.require("explorer").seen_row_name == "an exploration"


def test_run_exploration_without_a_dataset_is_rejected_before_it_starts(
    registry, fake_db
):
    """REQUIRES is enforced by ``__call__``, so a wiring mistake is not
    mistaken for an empty dataset."""
    with pytest.raises(UnitContractError, match="Context key 'dataset'"):
        RunExplorationUnit(explorer_id=11, explorer=_explorer())(ExecutionContext())


def test_an_unknown_explorer_is_reported_by_name(ctx, registry, fake_db):
    with pytest.raises(JobError, match="Explorer NoSuchExplorer not found in the reg"):
        RunExplorationUnit(
            explorer_id=11, explorer=_explorer(component="NoSuchExplorer")
        )(ctx)


def test_a_missing_explorer_row_is_reported_by_id(ctx, registry, fake_db):
    with pytest.raises(JobError, match="Explorer with id 99 not found."):
        RunExplorationUnit(explorer_id=99, explorer=_explorer())(ctx)


def test_a_column_absent_from_the_dataset_becomes_a_preparation_error(
    ctx, registry, fake_db
):
    fake_db["Explorer"][11].columns = [{"columnName": "nope"}]

    with pytest.raises(
        JobError, match="Error preparing the dataset for the exploration"
    ):
        RunExplorationUnit(explorer_id=11, explorer=_explorer())(ctx)


def test_a_failing_exploration_is_wrapped_with_the_component_name(
    ctx, registry, fake_db
):
    with pytest.raises(
        JobError, match="Error launching the exploration ExplodingExplorer."
    ) as excinfo:
        RunExplorationUnit(
            explorer_id=11, explorer=_explorer(component="ExplodingExplorer")
        )(ctx)

    assert "the exploration itself blew up" in str(excinfo.value.__cause__)


def test_two_exploration_units_do_not_share_a_resolved_class(ctx, registry, fake_db):
    """The registry lookup is memoized on the instance, not in the context.

    Two exploration nodes in one context must each resolve their own component;
    a context-global cache key would make the second silently reuse the first.
    """
    first = RunExplorationUnit(explorer_id=11, explorer=_explorer())
    second = RunExplorationUnit(
        explorer_id=11, explorer=_explorer(component="BadPathExplorer")
    )

    first(ctx)
    second(ctx)

    assert first._explorer_class is RecordingExplorer
    assert second._explorer_class is BadPathExplorer


# --- SaveExplorationUnit ------------------------------------------------


def test_save_exploration_writes_under_the_notebook_folder(
    ctx, registry, fake_db, notebook_path
):
    RunExplorationUnit(explorer_id=11, explorer=_explorer())(ctx)
    SaveExplorationUnit(explorer_id=11)(ctx)

    written = pathlib.Path(ctx.require("exploration_path"))
    assert written.exists()
    assert written.parent == notebook_path / "3"
    assert written.name == "11-x.txt"


def test_save_exploration_uses_the_explorer_that_ran(
    ctx, registry, fake_db, notebook_path
):
    """Identity, not equality: the saved file name carries state the instance
    was built with, so rebuilding a second explorer from the same config would
    pass this by accident. Asserting ``is`` is what makes it real."""
    RunExplorationUnit(explorer_id=11, explorer=_explorer(marker="carried"))(ctx)
    ran = ctx.require("explorer")

    SaveExplorationUnit(explorer_id=11)(ctx)

    assert ctx.require("explorer") is ran
    assert pathlib.Path(ctx.require("exploration_path")).name == "11-carried.txt"


def test_save_exploration_creates_the_notebook_folder_when_absent(
    ctx, registry, fake_db, notebook_path
):
    assert not notebook_path.exists()

    RunExplorationUnit(explorer_id=11, explorer=_explorer())(ctx)
    SaveExplorationUnit(explorer_id=11)(ctx)

    assert (notebook_path / "3").is_dir()


def test_save_exploration_without_a_result_is_rejected(
    registry, fake_db, notebook_path
):
    with pytest.raises(UnitContractError, match="Context key 'exploration_result'"):
        SaveExplorationUnit(explorer_id=11)(ExecutionContext())


def test_a_save_that_does_not_return_a_path_is_reported(
    ctx, registry, fake_db, notebook_path
):
    RunExplorationUnit(explorer_id=11, explorer=_explorer(component="BadPathExplorer"))(
        ctx
    )

    with pytest.raises(JobError, match="save path is not a pathlib.Path"):
        SaveExplorationUnit(explorer_id=11)(ctx)


def test_the_published_path_is_a_plain_string(ctx, registry, fake_db, notebook_path):
    """``exploration_path`` travels as a ref, so it has to be JSON data.

    A ``pathlib.Path`` would raise on ``put_ref``; this pins that the unit
    converts before publishing.
    """
    RunExplorationUnit(explorer_id=11, explorer=_explorer())(ctx)
    SaveExplorationUnit(explorer_id=11)(ctx)

    assert isinstance(ctx.to_dict()["exploration_path"], str)
