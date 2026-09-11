"""Contract tests for the prediction units, isolated from any orchestrating job.

The context is built by hand rather than through a job, which is what exposes
composability mistakes: a job always wires the context "correctly", so an
end-to-end run cannot tell a real contract from a lucky one.
"""

from pathlib import Path

import pytest
from kink import di

from DashAI.back.dataloaders.classes.dashai_dataset import (
    load_dataset,
    save_dataset,
    to_dashai_dataset,
)
from DashAI.back.job.base_job import JobError
from DashAI.back.units.context import ExecutionContext, UnitContractError
from DashAI.back.units.load_trained_model_unit import LoadTrainedModelUnit
from DashAI.back.units.load_training_dataset_unit import LoadTrainingDatasetUnit
from DashAI.back.units.predict_unit import PredictUnit
from DashAI.back.units.save_prediction_unit import SavePredictionUnit


class _RunRow:
    """Stand-in for a Run ORM row."""

    def __init__(self, model_name="RecordingModel", run_path="somewhere"):
        self.model_name = model_name
        self.run_path = run_path


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


class RecordingModel:
    """Model whose ``load`` is a staticmethod, the way every real one is."""

    loaded_from = None

    def __init__(self):
        self.seen_columns = None

    @staticmethod
    def load(filename):
        model = RecordingModel()
        RecordingModel.loaded_from = filename
        return model

    def predict(self, x):
        self.seen_columns = x.column_names
        return [0] * len(x)


class UnloadableModel(RecordingModel):
    @staticmethod
    def load(filename):
        raise OSError("the artifact is not there")


class RecordingTask:
    """Task that records the training dataset it was given for decoding."""

    seen_train_columns = None

    def process_predictions(self, train_dataset, y_pred_proba, output_column):
        RecordingTask.seen_train_columns = train_dataset.column_names
        return [f"label-{int(value)}" for value in y_pred_proba]

    def process_manual_input(self, rows, dataset_path):
        import pandas as pd
        import pyarrow as pa

        from DashAI.back.types.value_types import Integer

        frame = pd.DataFrame(rows)
        types = {name: Integer(arrow_type=pa.int64()) for name in frame.columns}
        return to_dashai_dataset(frame, types=types)


@pytest.fixture(name="registry")
def fixture_registry():
    registry = {
        "RecordingModel": {"class": RecordingModel},
        "UnloadableModel": {"class": UnloadableModel},
        "RecordingTask": {"class": RecordingTask},
    }
    di["component_registry"] = registry
    yield registry
    del di["component_registry"]


@pytest.fixture(name="fake_db")
def fixture_fake_db():
    rows = {"Run": {5: _RunRow()}}
    di["session_factory"] = _FakeSessionFactory(rows)
    yield rows
    del di["session_factory"]


def _dataset(**columns):
    import pandas as pd
    import pyarrow as pa

    from DashAI.back.types.value_types import Integer

    frame = pd.DataFrame(columns)
    types = {name: Integer(arrow_type=pa.int64()) for name in frame.columns}
    return to_dashai_dataset(frame, types=types)


@pytest.fixture(name="stored_training_dataset")
def fixture_stored_training_dataset(tmp_path):
    """A training dataset on disk, laid out the way a Dataset row points at it."""
    root = tmp_path / "training"
    save_dataset(_dataset(a=[1, 2, 3], b=[4, 5, 6]), str(root / "dataset"))
    return root


@pytest.fixture(name="datasets_path")
def fixture_datasets_path(tmp_path):
    config = {"DATASETS_PATH": tmp_path / "datasets"}
    di["config"] = config
    yield config["DATASETS_PATH"]
    del di["config"]


# --- LoadTrainedModelUnit -----------------------------------------------


def test_the_model_comes_from_the_path_the_run_recorded(registry, fake_db):
    """Neither the component nor the path is configuration: both are read off
    the run, so the model restored is always the one that run saved."""
    ctx = ExecutionContext()
    fake_db["Run"][5].run_path = "the/recorded/path"

    LoadTrainedModelUnit(run_id=5)(ctx)

    assert isinstance(ctx.require("model"), RecordingModel)
    assert RecordingModel.loaded_from == "the/recorded/path"


def test_a_missing_run_is_reported_by_id(registry, fake_db):
    with pytest.raises(JobError, match="Run 99 does not exist in DB."):
        LoadTrainedModelUnit(run_id=99)(ExecutionContext())


def test_an_unknown_model_name_is_reported_by_name(registry, fake_db):
    fake_db["Run"][5].model_name = "NoSuchModel"

    with pytest.raises(JobError, match="Model NoSuchModel not found in the registry"):
        LoadTrainedModelUnit(run_id=5)(ExecutionContext())


def test_an_artifact_that_cannot_be_read_names_the_model_and_the_path(
    registry, fake_db
):
    fake_db["Run"][5].model_name = "UnloadableModel"
    fake_db["Run"][5].run_path = "gone"

    with pytest.raises(
        JobError, match="Failed to load model UnloadableModel from path gone"
    ) as excinfo:
        LoadTrainedModelUnit(run_id=5)(ExecutionContext())

    assert "the artifact is not there" in str(excinfo.value.__cause__)


def test_two_model_units_do_not_share_a_resolved_class(registry, fake_db):
    """The registry lookup is memoized on the instance, not in the context."""
    fake_db["Run"][6] = _RunRow(model_name="UnloadableModel", run_path="gone")

    first = LoadTrainedModelUnit(run_id=5)
    second = LoadTrainedModelUnit(run_id=6)

    first(ExecutionContext())
    with pytest.raises(JobError):
        second(ExecutionContext())

    assert first._model_class is RecordingModel
    assert second._model_class is UnloadableModel


# --- LoadTrainingDatasetUnit --------------------------------------------


def test_the_training_dataset_lands_under_its_own_key(stored_training_dataset):
    """Not ``dataset``: this one is a reference for decoding and typing, and
    would otherwise collide with the dataset actually being predicted on."""
    ctx = ExecutionContext()

    LoadTrainingDatasetUnit(train_dataset_file_path=str(stored_training_dataset))(ctx)

    assert ctx.require("train_dataset").column_names == ["a", "b"]
    assert not ctx.has("dataset")


def test_the_training_dataset_can_coexist_with_the_one_being_predicted_on(
    stored_training_dataset,
):
    """The whole reason for the separate key: both datasets are live at once."""
    ctx = ExecutionContext()
    ctx.put("dataset", _dataset(a=[9], b=[9]))

    LoadTrainingDatasetUnit(train_dataset_file_path=str(stored_training_dataset))(ctx)

    assert ctx.require("dataset")["a"] == [9]
    assert ctx.require("train_dataset")["a"] == [1, 2, 3]


def test_the_declared_types_travel_as_plain_data(stored_training_dataset):
    """``train_dataset_types`` is a ref so the saving step never reopens the
    file. ``put_ref`` rejects anything that is not JSON data, which is what
    stops a live type object from being smuggled across the boundary — note
    ``to_string`` returns a dict despite its name.
    """
    import json

    ctx = ExecutionContext()

    LoadTrainingDatasetUnit(train_dataset_file_path=str(stored_training_dataset))(ctx)

    types = ctx.to_dict()["train_dataset_types"]
    assert types == {
        "a": {"type": "Integer", "dtype": "int64"},
        "b": {"type": "Integer", "dtype": "int64"},
    }
    json.dumps(types)


def test_an_unreadable_training_dataset_names_the_folder(tmp_path):
    with pytest.raises(JobError, match="Cannot load training dataset from"):
        LoadTrainingDatasetUnit(train_dataset_file_path=str(tmp_path / "nowhere"))(
            ExecutionContext()
        )


# --- PredictUnit --------------------------------------------------------


def _ready_context(stored_training_dataset, dataset=None):
    ctx = ExecutionContext()
    ctx.put("dataset", dataset if dataset is not None else _dataset(a=[1, 2], b=[3, 4]))
    ctx.put("model", RecordingModel())
    LoadTrainingDatasetUnit(train_dataset_file_path=str(stored_training_dataset))(ctx)
    return ctx


def _predict_unit(**overrides):
    config = {
        "task_name": "RecordingTask",
        "input_columns": ["a"],
        "output_columns": ["target"],
    }
    config.update(overrides)
    return PredictUnit(**config)


def test_predict_publishes_decoded_labels(registry, stored_training_dataset):
    ctx = _ready_context(stored_training_dataset)

    _predict_unit()(ctx)

    assert ctx.require("y_pred") == ["label-0", "label-0"]


def test_predict_hands_the_model_only_the_input_columns(
    registry, stored_training_dataset
):
    """Selected against the dataset in the context right now, so whatever
    produced it — a load or hand-typed rows — is free to differ in shape."""
    ctx = _ready_context(stored_training_dataset)

    _predict_unit()(ctx)

    assert ctx.require("model").seen_columns == ["a"]


def test_predict_decodes_against_the_training_dataset(
    registry, stored_training_dataset
):
    ctx = _ready_context(stored_training_dataset)

    _predict_unit()(ctx)

    assert RecordingTask.seen_train_columns == ["a", "b"]


def test_predict_validates_the_task_before_it_runs(registry, stored_training_dataset):
    """``validate`` is what the orchestrator calls early, so a missing task is
    reported as a task problem rather than being overtaken by a later failure."""
    with pytest.raises(JobError, match="Task NoSuchTask not found in the registry"):
        _predict_unit(task_name="NoSuchTask").validate(ExecutionContext())


def test_predict_without_a_model_is_rejected_before_it_starts(
    registry, stored_training_dataset
):
    ctx = ExecutionContext()
    ctx.put("dataset", _dataset(a=[1]))
    LoadTrainingDatasetUnit(train_dataset_file_path=str(stored_training_dataset))(ctx)

    with pytest.raises(UnitContractError, match="Context key 'model'"):
        _predict_unit()(ctx)


def test_predict_without_a_training_dataset_is_rejected_before_it_starts(registry):
    """A missing key means "the loader did not run", not "there is nothing to
    decode against" — so it has to fail loudly instead of predicting anyway."""
    ctx = ExecutionContext()
    ctx.put("dataset", _dataset(a=[1]))
    ctx.put("model", RecordingModel())

    with pytest.raises(UnitContractError, match="Context key 'train_dataset'"):
        _predict_unit()(ctx)


# --- SavePredictionUnit -------------------------------------------------


def _save_unit(**overrides):
    config = {"input_columns": ["a"], "output_columns": ["target"]}
    config.update(overrides)
    return SavePredictionUnit(**config)


def test_save_writes_the_inputs_plus_the_predicted_column(
    registry, stored_training_dataset, datasets_path
):
    ctx = _ready_context(stored_training_dataset)
    _predict_unit()(ctx)

    _save_unit()(ctx)

    saved = load_dataset(str(Path(ctx.require("results_path")) / "dataset"))
    assert saved.column_names == ["a", "b", "target"]
    assert saved["target"] == ["label-0", "label-0"]


def test_save_resolves_the_columns_against_the_dataset_it_is_handed(
    registry, stored_training_dataset, datasets_path
):
    """The column list is read at the top of execute, never published earlier.

    Here the dataset already carries a column named like the output one; it has
    to be replaced, not duplicated — which only works if the names are resolved
    from the dataset in hand.
    """
    ctx = _ready_context(
        stored_training_dataset, dataset=_dataset(a=[1, 2], target=[7, 8])
    )
    _predict_unit()(ctx)

    _save_unit()(ctx)

    saved = load_dataset(str(Path(ctx.require("results_path")) / "dataset"))
    assert saved.column_names == ["a", "target"]
    assert saved["target"] == ["label-0", "label-0"]


def test_two_saves_never_collide(registry, stored_training_dataset, datasets_path):
    """A prediction has no natural key to overwrite, so each run gets a folder."""
    ctx = _ready_context(stored_training_dataset)
    _predict_unit()(ctx)

    _save_unit()(ctx)
    first = ctx.require("results_path")
    _save_unit()(ctx)
    second = ctx.require("results_path")

    assert first != second
    assert Path(first).exists()
    assert Path(second).exists()


def test_save_without_a_prediction_is_rejected_before_it_starts(
    registry, stored_training_dataset, datasets_path
):
    ctx = ExecutionContext()
    ctx.put("dataset", _dataset(a=[1]))
    ctx.put_ref("train_dataset_types", {})

    with pytest.raises(UnitContractError, match="Context key 'y_pred'"):
        _save_unit()(ctx)


def test_the_published_results_path_is_a_plain_string(
    registry, stored_training_dataset, datasets_path
):
    """``results_path`` travels as a ref, so it has to be JSON data."""
    ctx = _ready_context(stored_training_dataset)
    _predict_unit()(ctx)

    _save_unit()(ctx)

    assert isinstance(ctx.to_dict()["results_path"], str)
