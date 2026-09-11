"""Tests for SaveModelUnit's contract, independent of a real model or disk."""

import os

import pytest
from kink import di

from DashAI.back.job.base_job import JobError
from DashAI.back.units.context import ExecutionContext, UnitContractError
from DashAI.back.units.save_model_unit import SaveModelUnit


class _RecordingModel:
    """Stands in for a trained model, recording where it was asked to go.

    It writes a real file at that path, because the save is now made atomic:
    the model is handed a temporary path and what it leaves there is moved
    into place. A double that recorded without writing would leave nothing to
    move, which is the same failure a model that silently saved nothing would
    produce -- and is exactly what should be reported rather than hidden.
    """

    def __init__(self) -> None:
        self.saved_to = None

    def save(self, path) -> None:
        self.saved_to = path
        with open(path, "w", encoding="utf-8") as file:
            file.write("a saved model")


@pytest.fixture(name="runs_path")
def fixture_runs_path(tmp_path):
    di["config"] = {"RUNS_PATH": str(tmp_path)}
    yield str(tmp_path)
    del di["config"]


def test_the_model_lands_in_a_directory_named_by_the_prefix(runs_path):
    ctx = ExecutionContext()
    model = _RecordingModel()
    ctx.put("model", model)

    SaveModelUnit(artifact_prefix="pipeline-3-save")(ctx)

    # Where the artifact ended up, not where the model was told to write. The
    # save is atomic, so the model writes to a temporary sibling and what it
    # left there is moved into place; the destination is what the caller and
    # the row care about.
    expected = os.path.join(runs_path, "pipeline-3-save")
    assert os.path.exists(expected)
    assert ctx.require("model_path") == expected


def test_a_numeric_run_id_is_a_valid_prefix(runs_path):
    """The path a real run writes to has to keep working unchanged.

    ``ModelJob`` passes ``str(run.id)``, and
    ``test_model_job_orchestration.py`` asserts the directory is named exactly
    that. A guard that rejected it would break every training run.
    """
    ctx = ExecutionContext()
    model = _RecordingModel()
    ctx.put("model", model)

    SaveModelUnit(artifact_prefix="17")(ctx)

    assert os.path.exists(os.path.join(runs_path, "17"))
    assert ctx.require("model_path") == os.path.join(runs_path, "17")


@pytest.mark.parametrize(
    "prefix",
    ["../escape", "a/b", "a\b", "", "C:nope", ".", "with space"],
)
def test_a_prefix_that_could_be_read_as_a_path_is_refused(runs_path, prefix):
    """A prefix is a directory name, so it must not be able to leave RUNS_PATH.

    ``os.path.join`` with a separator or a parent reference in the prefix
    happily produces a destination outside the runs directory, and the model
    would be written there without any error.
    """
    ctx = ExecutionContext()
    model = _RecordingModel()
    ctx.put("model", model)

    with pytest.raises(JobError, match="artifact prefix"):
        SaveModelUnit(artifact_prefix=prefix)(ctx)

    assert model.saved_to is None


def test_validate_runs_before_anything_is_written(runs_path):
    """``__call__`` validates first, so a bad prefix never reaches ``save``."""
    unit = SaveModelUnit(artifact_prefix="../escape")
    ctx = ExecutionContext()
    ctx.put("model", _RecordingModel())

    with pytest.raises(JobError):
        unit.validate(ctx)


def test_the_unit_still_needs_a_model(runs_path):
    """``run_id`` left REQUIRES; ``model`` did not."""
    with pytest.raises(UnitContractError, match="'model'"):
        SaveModelUnit(artifact_prefix="1")(ExecutionContext())


def test_a_save_that_dies_halfway_leaves_the_previous_artifact_alone(runs_path):
    """The reason the save is atomic.

    A model that raises partway through writing used to leave a truncated
    artifact at the destination, which the row then pointed at as if it were a
    model. Now the destination is only replaced once the new one is complete.
    """
    destination = os.path.join(runs_path, "42")
    with open(destination, "w", encoding="utf-8") as file:
        file.write("the previous model")

    class _DyingModel:
        def save(self, path):
            with open(path, "w", encoding="utf-8") as file:
                file.write("half a model")
            raise RuntimeError("out of disk")

    ctx = ExecutionContext()
    ctx.put("model", _DyingModel())

    with pytest.raises(JobError, match="Model saving failed"):
        SaveModelUnit(artifact_prefix="42")(ctx)

    with open(destination, encoding="utf-8") as file:
        assert file.read() == "the previous model"
    # And nothing half-written was left lying next to it.
    assert os.listdir(runs_path) == ["42"]
