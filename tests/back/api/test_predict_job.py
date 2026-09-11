"""End-to-end regression net for ``PredictJob``.

Written before the job is decomposed into atomic units, and asserted against the
monolithic implementation, so that the refactor has something to be measured
against. The assertions are deliberately explicit — exact status values, exact
columns on disk, exact error message fragments — instead of the looser
``status in ["finished", "error"]`` style used elsewhere in this suite, which
cannot tell a unit that silently stopped doing part of its work from one that
did it.

``test_predict_api.py`` does not cover this: it enqueues the job and then only
exercises the CRUD endpoints, never checking the job's outcome nor the
``Prediction`` row.

Tests named ``test_currently_*`` pin behaviour that is known to be wrong. They
exist so the refactor can be proven behaviour-preserving first; the fix lands
afterwards as its own change, which flips the assertion and renames the test.

Lives under ``tests/back/api`` to reuse the ``client`` and ``dataset_1``
fixtures from this package's ``conftest.py``.
"""

import json
import shutil
from pathlib import Path

import pytest
from fastapi.exceptions import HTTPException
from fastapi.testclient import TestClient

from DashAI.back.core.enums.status import PredictionStatus
from DashAI.back.dataloaders.classes.dashai_dataset import load_dataset
from DashAI.back.dependencies.database.models import (
    Dataset,
    ModelSession,
    Prediction,
    Run,
)
from DashAI.back.job.base_job import JobError
from DashAI.back.job.model_job import ModelJob
from DashAI.back.job.predict_job import PredictJob

INPUT_COLUMNS = [
    "SepalLengthCm",
    "SepalWidthCm",
    "PetalLengthCm",
    "PetalWidthCm",
]
OUTPUT_COLUMN = "Species"
IRIS_ROWS = 150

SPLITS = json.dumps(
    {
        # The session names the splitter that produced its partitions, which is
        # how every consumer of Run.split_indexes tells a holdout payload from
        # a fold one.
        "splitter_name": "HoldoutSplitter",
        "splitType": "random",
        "train": 0.5,
        "test": 0.2,
        "validation": 0.3,
        "is_random": True,
        "has_changed": True,
        "seed": 42,
        "shuffle": True,
        "stratify": False,
    }
)


@pytest.fixture(scope="module", name="model_session_id")
def create_model_session(client: TestClient, dataset_1: Dataset):
    session_factory = client.app.container["session_factory"]

    with session_factory() as db:
        model_session = ModelSession(
            dataset_id=dataset_1.id,
            name="PredictJobSession",
            task_name="TabularClassificationTask",
            input_columns=INPUT_COLUMNS,
            output_columns=[OUTPUT_COLUMN],
            train_metrics=[],
            validation_metrics=[],
            test_metrics=[],
            evaluation_strategy="HoldoutEvaluationStrategy",
            splits=SPLITS,
        )
        db.add(model_session)
        db.commit()
        db.refresh(model_session)
        return model_session.id


@pytest.fixture(scope="module", name="trained_run_id")
def create_trained_run(client: TestClient, model_session_id: int):
    """A genuinely trained run: the prediction path loads the model from disk."""
    session_factory = client.app.container["session_factory"]

    with session_factory() as db:
        run = Run(
            model_session_id=model_session_id,
            optimizer_name="OptunaOptimizer",
            optimizer_parameters={
                "n_trials": 1,
                "sampler": "TPESampler",
                "pruner": "None",
            },
            model_name="KNeighborsClassifier",
            parameters={},
            name="PredictJobRun",
            goal_metric="Accuracy",
        )
        db.add(run)
        db.commit()
        db.refresh(run)
        run_id = run.id

    ModelJob(run_id=run_id).run()

    with session_factory() as db:
        run = db.get(Run, run_id)
        assert run.run_path, "the run fixture did not produce a saved model"
    return run_id


def _create_prediction(client, run_id, dataset_id=None):
    response = client.post(
        "/api/v1/predict/",
        json={"run_id": run_id, "dataset_id": dataset_id},
    )
    assert response.status_code == 200, response.text
    return response.json()["id"]


def _make_prediction_dataset(client, dataset_1: Dataset):
    """A throwaway copy of the iris dataset, safe for a test to destroy."""
    import uuid

    config = client.app.container["config"]
    session_factory = client.app.container["session_factory"]

    folder = Path(config["DATASETS_PATH"]) / f"predict-job-{uuid.uuid4()}"
    shutil.copytree(Path(dataset_1.file_path), folder)

    with session_factory() as db:
        row = Dataset(name=folder.name, file_path=str(folder))
        db.add(row)
        db.commit()
        db.refresh(row)
        db.expunge(row)
        return row


def _stored_prediction(client, prediction_id):
    session_factory = client.app.container["session_factory"]
    with session_factory() as db:
        prediction = db.get(Prediction, prediction_id)
        return {
            "status": prediction.status,
            "results_path": prediction.results_path,
            "start_time": prediction.start_time,
            "end_time": prediction.end_time,
        }


@pytest.fixture(name="restore_run")
def fixture_restore_run(client: TestClient, trained_run_id: int):
    """Let a test corrupt the module-scoped Run row and put it back after.

    The run and the model session are module scoped because training is slow;
    without this the error-branch tests would poison every test after them.
    """
    session_factory = client.app.container["session_factory"]
    with session_factory() as db:
        run = db.get(Run, trained_run_id)
        original = {"model_name": run.model_name, "run_path": run.run_path}

    yield

    with session_factory() as db:
        run = db.get(Run, trained_run_id)
        run.model_name = original["model_name"]
        run.run_path = original["run_path"]
        db.commit()


@pytest.fixture(name="restore_model_session")
def fixture_restore_model_session(client: TestClient, model_session_id: int):
    """Same idea for the module-scoped ModelSession row."""
    session_factory = client.app.container["session_factory"]
    with session_factory() as db:
        session_row = db.get(ModelSession, model_session_id)
        original = {
            "dataset_id": session_row.dataset_id,
            "task_name": session_row.task_name,
            "input_columns": list(session_row.input_columns),
            "output_columns": list(session_row.output_columns),
        }

    yield

    with session_factory() as db:
        session_row = db.get(ModelSession, model_session_id)
        for key, value in original.items():
            setattr(session_row, key, value)
        db.commit()


def test_predict_job_writes_the_predictions_and_finishes(
    client, trained_run_id, dataset_1
):
    """The happy path, end to end: status transitions and the dataset on disk.

    The saved dataset carries the input columns plus the predicted output
    column, one row per row of the input.
    """
    prediction_id = _create_prediction(client, trained_run_id, dataset_1.id)

    PredictJob(prediction_id=prediction_id).run()

    stored = _stored_prediction(client, prediction_id)
    assert stored["status"] == PredictionStatus.FINISHED
    assert stored["start_time"] is not None
    assert stored["end_time"] is not None
    assert stored["results_path"] is not None

    saved = load_dataset(str(Path(stored["results_path"]) / "dataset"))
    assert saved.column_names == INPUT_COLUMNS + [OUTPUT_COLUMN]
    assert len(saved) == IRIS_ROWS


def test_each_prediction_gets_its_own_results_folder(client, trained_run_id, dataset_1):
    """The destination is a fresh uuid folder, so two runs never collide."""
    first = _create_prediction(client, trained_run_id, dataset_1.id)
    second = _create_prediction(client, trained_run_id, dataset_1.id)

    PredictJob(prediction_id=first).run()
    PredictJob(prediction_id=second).run()

    first_path = _stored_prediction(client, first)["results_path"]
    second_path = _stored_prediction(client, second)["results_path"]

    assert first_path != second_path
    assert Path(first_path).exists()
    assert Path(second_path).exists()


def test_manual_input_predicts_without_a_dataset(client, trained_run_id):
    """The manual branch builds the instances from typed values instead of disk."""
    prediction_id = _create_prediction(client, trained_run_id, dataset_id=None)

    PredictJob(
        prediction_id=prediction_id,
        manual_input_data=[
            {
                "SepalLengthCm": 5.1,
                "SepalWidthCm": 3.5,
                "PetalLengthCm": 1.4,
                "PetalWidthCm": 0.2,
            }
        ],
    ).run()

    stored = _stored_prediction(client, prediction_id)
    assert stored["status"] == PredictionStatus.FINISHED

    saved = load_dataset(str(Path(stored["results_path"]) / "dataset"))
    assert saved.column_names == INPUT_COLUMNS + [OUTPUT_COLUMN]
    assert len(saved) == 1


def test_neither_a_dataset_nor_manual_input_is_rejected(client, trained_run_id):
    prediction_id = _create_prediction(client, trained_run_id, dataset_id=None)

    with pytest.raises(
        JobError, match="Either dataset_id or manual_input_data must be provided."
    ):
        PredictJob(prediction_id=prediction_id).run()

    assert _stored_prediction(client, prediction_id)["status"] == PredictionStatus.ERROR


def test_a_missing_prediction_row_is_a_404(client):
    with pytest.raises(HTTPException) as excinfo:
        PredictJob(prediction_id=999999).run()

    assert excinfo.value.status_code == 404
    assert excinfo.value.detail == "Prediction not found for id 999999"


def test_an_unknown_model_name_reports_it_and_errors(
    client, trained_run_id, dataset_1, restore_run
):
    prediction_id = _create_prediction(client, trained_run_id, dataset_1.id)

    session_factory = client.app.container["session_factory"]
    with session_factory() as db:
        db.get(Run, trained_run_id).model_name = "ThisModelDoesNotExist"
        db.commit()

    with pytest.raises(
        JobError, match="Model ThisModelDoesNotExist not found in the registry"
    ):
        PredictJob(prediction_id=prediction_id).run()

    assert _stored_prediction(client, prediction_id)["status"] == PredictionStatus.ERROR


def test_a_model_that_cannot_be_loaded_reports_the_path_and_errors(
    client, trained_run_id, dataset_1, restore_run
):
    prediction_id = _create_prediction(client, trained_run_id, dataset_1.id)

    session_factory = client.app.container["session_factory"]
    with session_factory() as db:
        db.get(Run, trained_run_id).run_path = "nowhere/at/all"
        db.commit()

    with pytest.raises(
        JobError,
        match="Failed to load model KNeighborsClassifier from path nowhere/at/all",
    ):
        PredictJob(prediction_id=prediction_id).run()

    assert _stored_prediction(client, prediction_id)["status"] == PredictionStatus.ERROR


def test_an_unknown_task_name_reports_it_and_errors(
    client, trained_run_id, dataset_1, restore_model_session, model_session_id
):
    """The task is resolved before the model, so this is the first error seen."""
    prediction_id = _create_prediction(client, trained_run_id, dataset_1.id)

    session_factory = client.app.container["session_factory"]
    with session_factory() as db:
        db.get(ModelSession, model_session_id).task_name = "ThisTaskDoesNotExist"
        db.commit()

    with pytest.raises(
        JobError, match="Task ThisTaskDoesNotExist not found in the registry"
    ):
        PredictJob(prediction_id=prediction_id).run()

    assert _stored_prediction(client, prediction_id)["status"] == PredictionStatus.ERROR


def test_a_model_session_without_input_columns_is_a_422(
    client, trained_run_id, dataset_1, restore_model_session, model_session_id
):
    prediction_id = _create_prediction(client, trained_run_id, dataset_1.id)

    session_factory = client.app.container["session_factory"]
    with session_factory() as db:
        db.get(ModelSession, model_session_id).input_columns = []
        db.commit()

    with pytest.raises(HTTPException) as excinfo:
        PredictJob(prediction_id=prediction_id).run()

    assert excinfo.value.status_code == 422
    assert excinfo.value.detail == "Model session has no input columns configured"
    assert _stored_prediction(client, prediction_id)["status"] == PredictionStatus.ERROR


def test_a_missing_training_dataset_row_leaves_the_row_in_error(
    client, trained_run_id, dataset_1, restore_model_session, model_session_id
):
    """The 404 must also mark the prediction as failed.

    This branch used to skip ``set_status_as_error``, unlike every one around
    it, so the row stayed STARTED forever — nothing else marks it, because the
    Huey error signal only writes to its own ``task_copy`` table and
    ``_execute_base_job`` calls ``run()`` with no handler.
    """
    prediction_id = _create_prediction(client, trained_run_id, dataset_1.id)

    session_factory = client.app.container["session_factory"]
    with session_factory() as db:
        db.get(ModelSession, model_session_id).dataset_id = 999999
        db.commit()

    with pytest.raises(HTTPException) as excinfo:
        PredictJob(prediction_id=prediction_id).run()

    assert excinfo.value.status_code == 404
    assert excinfo.value.detail == "Training dataset not found"
    assert _stored_prediction(client, prediction_id)["status"] == PredictionStatus.ERROR


def test_an_unreadable_training_dataset_leaves_the_row_in_error(
    client, trained_run_id, dataset_1, tmp_path
):
    """Same omission as above, on the branch that reads the training dataset.

    The message still has to be the specific one, not the generic prediction
    wrapper: this load happens before the dataset to predict on is even
    touched, and that ordering is what the message depends on.
    """
    prediction_id = _create_prediction(client, trained_run_id, dataset_1.id)

    stored_folder = Path(dataset_1.file_path) / "dataset"
    backup = tmp_path / "training-dataset-backup"
    shutil.copytree(stored_folder, backup)
    shutil.rmtree(stored_folder)
    try:
        with pytest.raises(JobError, match="Cannot load training dataset from"):
            PredictJob(prediction_id=prediction_id).run()

        assert (
            _stored_prediction(client, prediction_id)["status"]
            == PredictionStatus.ERROR
        )
    finally:
        shutil.copytree(backup, stored_folder)


def test_an_unreadable_prediction_dataset_is_reported_as_a_prediction_failure(
    client, trained_run_id, dataset_1, tmp_path
):
    """Loading the dataset to predict on shares the "prediction failed" wrapper.

    Unlike the *training* dataset, which has a message of its own, the
    inference dataset is loaded inside the same ``try`` as the prediction, so a
    read failure surfaces as the generic message with the real cause attached.
    Pinned because it is the exact spot a unit boundary lands on, and an
    improved message here would be a silent behaviour change.
    """
    prediction_dataset = _make_prediction_dataset(client, dataset_1)
    prediction_id = _create_prediction(client, trained_run_id, prediction_dataset.id)

    shutil.rmtree(Path(prediction_dataset.file_path) / "dataset")

    with pytest.raises(JobError, match="Model prediction failed"):
        PredictJob(prediction_id=prediction_id).run()

    assert _stored_prediction(client, prediction_id)["status"] == PredictionStatus.ERROR


def test_a_prediction_that_blows_up_leaves_the_row_in_error(
    client, trained_run_id, dataset_1, monkeypatch
):
    """Any unexpected failure while predicting is reported as one message."""
    from DashAI.back.models.scikit_learn.k_neighbors_classifier import (
        KNeighborsClassifier,
    )

    prediction_id = _create_prediction(client, trained_run_id, dataset_1.id)

    def _explode(self, x):
        raise RuntimeError("the model itself blew up")

    monkeypatch.setattr(KNeighborsClassifier, "predict", _explode)

    with pytest.raises(JobError, match="Model prediction failed") as excinfo:
        PredictJob(prediction_id=prediction_id).run()

    assert "the model itself blew up" in str(excinfo.value.__cause__)
    assert _stored_prediction(client, prediction_id)["status"] == PredictionStatus.ERROR


def test_a_type_error_while_predicting_leaves_the_row_in_error(
    client, trained_run_id, dataset_1, monkeypatch
):
    """The ``TypeError`` branch is still a 400, but now it marks the row too.

    Its ``ValueError`` neighbour always did; this one did not, so a type
    mismatch left the prediction STARTED forever.
    """
    from DashAI.back.models.scikit_learn.k_neighbors_classifier import (
        KNeighborsClassifier,
    )

    prediction_id = _create_prediction(client, trained_run_id, dataset_1.id)

    def _wrong_type(self, x):
        raise TypeError("bad type somewhere in the input")

    monkeypatch.setattr(KNeighborsClassifier, "predict", _wrong_type)

    # JobError rather than HTTPException: the exception leaves the worker
    # through dill, which an HTTPException does not survive.
    with pytest.raises(JobError) as excinfo:
        PredictJob(prediction_id=prediction_id).run()

    assert "Type validation failed" in str(excinfo.value)
    assert _stored_prediction(client, prediction_id)["status"] == PredictionStatus.ERROR


def test_a_value_error_while_predicting_leaves_the_row_in_error(
    client, trained_run_id, dataset_1, monkeypatch
):
    """The ``ValueError`` branch is reported as a JobError and marks the row."""
    from DashAI.back.models.scikit_learn.k_neighbors_classifier import (
        KNeighborsClassifier,
    )

    prediction_id = _create_prediction(client, trained_run_id, dataset_1.id)

    def _bad_value(self, x):
        raise ValueError("a value the model cannot use")

    monkeypatch.setattr(KNeighborsClassifier, "predict", _bad_value)

    # JobError rather than HTTPException: the exception leaves the worker
    # through dill, which an HTTPException does not survive.
    with pytest.raises(JobError) as excinfo:
        PredictJob(prediction_id=prediction_id).run()

    assert "Invalid input data" in str(excinfo.value)
    assert _stored_prediction(client, prediction_id)["status"] == PredictionStatus.ERROR


def test_set_status_as_delivered_marks_the_row(client, trained_run_id, dataset_1):
    prediction_id = _create_prediction(client, trained_run_id, dataset_1.id)

    PredictJob(prediction_id=prediction_id).set_status_as_delivered()

    assert (
        _stored_prediction(client, prediction_id)["status"]
        == PredictionStatus.DELIVERED
    )
