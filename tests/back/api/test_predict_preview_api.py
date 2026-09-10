"""End-to-end regression net for ``POST /predict/preview``.

The synchronous counterpart of ``PredictJob``: same prediction, no persistence,
and errors reported as HTTP responses instead of ``JobError``. Written before
``run_manual_prediction`` is decomposed into the same units the job uses, and
asserted against the pre-refactor implementation, so the refactor has something
to be measured against.

Every failure mode gets its own test with its exact status code and detail
string, because that is the whole contract this endpoint has with the frontend's
manual-prediction form: eleven distinct responses, four status codes. A
migration that turned any of them into a generic 500 would be a silent UX
regression in the one feature the endpoint exists for.

This endpoint had no tests at all before this file.

Lives under ``tests/back/api`` to reuse the ``client`` and ``dataset_1``
fixtures from this package's ``conftest.py``.
"""

import json
import shutil
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from DashAI.back.dependencies.database.models import Dataset, ModelSession, Run
from DashAI.back.job.model_job import ModelJob

INPUT_COLUMNS = [
    "SepalLengthCm",
    "SepalWidthCm",
    "PetalLengthCm",
    "PetalWidthCm",
]
OUTPUT_COLUMN = "Species"

A_ROW = {
    "SepalLengthCm": 5.1,
    "SepalWidthCm": 3.5,
    "PetalLengthCm": 1.4,
    "PetalWidthCm": 0.2,
}

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
            name="PreviewSession",
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
    """A genuinely trained run: the preview path loads the model from disk."""
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
            name="PreviewRun",
            goal_metric="Accuracy",
        )
        db.add(run)
        db.commit()
        db.refresh(run)
        run_id = run.id

    ModelJob(run_id=run_id).run()

    with session_factory() as db:
        assert db.get(Run, run_id).run_path, "the fixture did not save a model"
    return run_id


def _preview(client, run_id, rows=None):
    return client.post(
        "/api/v1/predict/preview",
        data={
            "run_id": str(run_id),
            "manual_input_data": json.dumps(rows if rows is not None else [A_ROW]),
        },
    )


@pytest.fixture(name="restore_run")
def fixture_restore_run(client: TestClient, trained_run_id: int):
    """Let a test corrupt the module-scoped Run row and put it back after.

    The run is module scoped because training is slow; without this the
    error-branch tests would poison every test after them.
    """
    session_factory = client.app.container["session_factory"]
    with session_factory() as db:
        run = db.get(Run, trained_run_id)
        original = {
            "model_name": run.model_name,
            "run_path": run.run_path,
            "model_session_id": run.model_session_id,
        }

    yield

    with session_factory() as db:
        run = db.get(Run, trained_run_id)
        for key, value in original.items():
            setattr(run, key, value)
        db.commit()


@pytest.fixture(name="restore_model_session")
def fixture_restore_model_session(client: TestClient, model_session_id: int):
    """Same idea for the module-scoped ModelSession row."""
    session_factory = client.app.container["session_factory"]
    with session_factory() as db:
        row = db.get(ModelSession, model_session_id)
        original = {
            "dataset_id": row.dataset_id,
            "task_name": row.task_name,
            "input_columns": list(row.input_columns),
            "output_columns": list(row.output_columns),
        }

    yield

    with session_factory() as db:
        row = db.get(ModelSession, model_session_id)
        for key, value in original.items():
            setattr(row, key, value)
        db.commit()


# --- the happy path -----------------------------------------------------


def test_the_preview_returns_the_inputs_plus_the_prediction(client, trained_run_id):
    response = _preview(client, trained_run_id)

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["columns"] == INPUT_COLUMNS + [OUTPUT_COLUMN]
    assert len(body["rows"]) == 1
    assert body["rows"][0][:4] == [5.1, 3.5, 1.4, 0.2]
    # The label is decoded against the training dataset, not left as an index.
    assert body["rows"][0][4] in {"Iris-setosa", "Iris-versicolor", "Iris-virginica"}


def test_the_preview_handles_several_rows_at_once(client, trained_run_id):
    rows = [A_ROW, {**A_ROW, "PetalLengthCm": 5.9, "PetalWidthCm": 2.1}]

    response = _preview(client, trained_run_id, rows)

    assert response.status_code == 200, response.text
    body = response.json()
    assert len(body["rows"]) == 2
    assert body["rows"][1][2] == 5.9


def test_the_preview_and_the_job_agree_on_the_same_input(client, trained_run_id):
    """The point of sharing units: the two paths cannot answer differently.

    Same hand-typed row, one predicted synchronously for the preview and one
    through ``PredictJob``. They used to run separate copies of the same three
    steps, so nothing stopped them from drifting apart; this is what would fail
    if the prediction were ever fixed in one place only.
    """
    from DashAI.back.dataloaders.classes.dashai_dataset import load_dataset
    from DashAI.back.dependencies.database.models import Prediction
    from DashAI.back.job.predict_job import PredictJob

    row = {**A_ROW, "PetalLengthCm": 4.7, "PetalWidthCm": 1.4}

    previewed = _preview(client, trained_run_id, [row])
    assert previewed.status_code == 200, previewed.text
    preview_label = previewed.json()["rows"][0][4]

    created = client.post(
        "/api/v1/predict/", json={"run_id": trained_run_id, "dataset_id": None}
    )
    assert created.status_code == 200, created.text
    prediction_id = created.json()["id"]

    PredictJob(prediction_id=prediction_id, manual_input_data=[row]).run()

    session_factory = client.app.container["session_factory"]
    with session_factory() as db:
        results_path = db.get(Prediction, prediction_id).results_path

    saved = load_dataset(str(Path(results_path) / "dataset"))
    assert saved[OUTPUT_COLUMN] == [preview_label]


def test_the_preview_persists_nothing(client, trained_run_id):
    """It is a preview: no Prediction row, no results folder."""
    from DashAI.back.dependencies.database.models import Prediction

    session_factory = client.app.container["session_factory"]
    with session_factory() as db:
        before = db.query(Prediction).count()

    assert _preview(client, trained_run_id).status_code == 200

    with session_factory() as db:
        assert db.query(Prediction).count() == before


# --- the four 404/422 checks the endpoint owns --------------------------


def test_a_missing_run_is_a_404(client):
    response = _preview(client, 999999)

    assert response.status_code == 404
    assert response.json()["detail"] == "Run not found for id 999999"


def test_a_missing_model_session_is_a_404(client, trained_run_id, restore_run):
    session_factory = client.app.container["session_factory"]
    with session_factory() as db:
        db.get(Run, trained_run_id).model_session_id = 999999
        db.commit()

    response = _preview(client, trained_run_id)

    assert response.status_code == 404
    assert response.json()["detail"] == "Model session not found"


def test_a_missing_training_dataset_row_is_a_404(
    client, trained_run_id, restore_model_session, model_session_id
):
    session_factory = client.app.container["session_factory"]
    with session_factory() as db:
        db.get(ModelSession, model_session_id).dataset_id = 999999
        db.commit()

    response = _preview(client, trained_run_id)

    assert response.status_code == 404
    assert response.json()["detail"] == "Training dataset not found"


def test_no_input_columns_is_a_422(
    client, trained_run_id, restore_model_session, model_session_id
):
    session_factory = client.app.container["session_factory"]
    with session_factory() as db:
        db.get(ModelSession, model_session_id).input_columns = []
        db.commit()

    response = _preview(client, trained_run_id)

    assert response.status_code == 422
    assert response.json()["detail"] == "Model session has no input columns configured"


def test_no_output_columns_is_a_422(
    client, trained_run_id, restore_model_session, model_session_id
):
    session_factory = client.app.container["session_factory"]
    with session_factory() as db:
        db.get(ModelSession, model_session_id).output_columns = []
        db.commit()

    response = _preview(client, trained_run_id)

    assert response.status_code == 422
    assert response.json()["detail"] == "Model session has no output columns configured"


# --- the registry and loading failures ----------------------------------


def test_an_unknown_task_is_a_500_naming_the_task(
    client, trained_run_id, restore_model_session, model_session_id
):
    """The task is resolved before the model, so this wins when both are wrong.

    That ordering is behaviour: it decides which of the two the user is told
    about, and a decomposition that resolves the model first would change it.
    """
    session_factory = client.app.container["session_factory"]
    with session_factory() as db:
        db.get(ModelSession, model_session_id).task_name = "NoSuchTask"
        db.commit()

    response = _preview(client, trained_run_id)

    assert response.status_code == 500
    assert response.json()["detail"] == "Task NoSuchTask not found in the registry"


def test_an_unknown_model_is_a_500_naming_the_model(
    client, trained_run_id, restore_run
):
    session_factory = client.app.container["session_factory"]
    with session_factory() as db:
        db.get(Run, trained_run_id).model_name = "NoSuchModel"
        db.commit()

    response = _preview(client, trained_run_id)

    assert response.status_code == 500
    assert response.json()["detail"] == "Model NoSuchModel not found in the registry"


def test_an_unreadable_model_is_a_500_naming_model_and_path(
    client, trained_run_id, restore_run
):
    session_factory = client.app.container["session_factory"]
    with session_factory() as db:
        db.get(Run, trained_run_id).run_path = "nowhere/at/all"
        db.commit()

    response = _preview(client, trained_run_id)

    assert response.status_code == 500
    assert response.json()["detail"] == (
        "Failed to load model KNeighborsClassifier from path nowhere/at/all"
    )


def test_an_unreadable_training_dataset_is_a_500_without_the_path(
    client, trained_run_id, dataset_1, tmp_path
):
    """The detail is deliberately bare here — no path, unlike the model error.

    Pinned exactly because the unit that replaces this step reports a message of
    its own that *does* carry the path; the endpoint has to keep saying this.
    """
    stored = Path(dataset_1.file_path) / "dataset"
    backup = tmp_path / "training-dataset-backup"
    shutil.copytree(stored, backup)
    shutil.rmtree(stored)
    try:
        response = _preview(client, trained_run_id)

        assert response.status_code == 500
        assert response.json()["detail"] == "Cannot load training dataset"
    finally:
        shutil.copytree(backup, stored)


# --- the input and prediction failures ----------------------------------


def test_an_unknown_input_column_is_a_400(client, trained_run_id):
    response = _preview(client, trained_run_id, [{"NotAColumn": 1.0}])

    assert response.status_code == 400
    detail = response.json()["detail"]
    assert detail.startswith("Invalid input data: ")
    assert "NotAColumn" in detail


def test_a_value_error_while_predicting_is_a_400(client, trained_run_id, monkeypatch):
    from DashAI.back.models.scikit_learn.k_neighbors_classifier import (
        KNeighborsClassifier,
    )

    def _bad_value(self, x):
        raise ValueError("a value the model cannot use")

    monkeypatch.setattr(KNeighborsClassifier, "predict", _bad_value)

    response = _preview(client, trained_run_id)

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "Invalid input data: a value the model cannot use"
    )


def test_a_type_error_while_predicting_is_also_a_400_invalid_input(
    client, trained_run_id, monkeypatch
):
    """The sync path merges ``TypeError`` into the ``ValueError`` message.

    ``PredictJob`` keeps them apart ("Type validation failed" vs "Invalid input
    data"). That divergence is pinned on both sides so neither drifts into the
    other while they share units.
    """
    from DashAI.back.models.scikit_learn.k_neighbors_classifier import (
        KNeighborsClassifier,
    )

    def _wrong_type(self, x):
        raise TypeError("bad type somewhere in the input")

    monkeypatch.setattr(KNeighborsClassifier, "predict", _wrong_type)

    response = _preview(client, trained_run_id)

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "Invalid input data: bad type somewhere in the input"
    )


def test_any_other_prediction_failure_is_a_500(client, trained_run_id, monkeypatch):
    from DashAI.back.models.scikit_learn.k_neighbors_classifier import (
        KNeighborsClassifier,
    )

    def _explode(self, x):
        raise RuntimeError("the model itself blew up")

    monkeypatch.setattr(KNeighborsClassifier, "predict", _explode)

    response = _preview(client, trained_run_id)

    assert response.status_code == 500
    assert response.json()["detail"] == "Model prediction failed"


# --- the request-shape checks, owned by the endpoint itself -------------


@pytest.mark.parametrize(
    ("payload", "detail"),
    [
        ({}, "Missing run_id or manual_input_data"),
        (
            {"run_id": "notanint", "manual_input_data": "[]"},
            "Invalid run_id: notanint",
        ),
        (
            {"run_id": "1", "manual_input_data": "[]"},
            "manual_input_data must be a non-empty JSON array of objects (list[dict]).",
        ),
        (
            {"run_id": "1", "manual_input_data": "[1, 2]"},
            "Each item in manual_input_data must be a JSON object (dict).",
        ),
    ],
)
def test_the_request_shape_is_validated_before_anything_is_loaded(
    client, payload, detail
):
    response = client.post("/api/v1/predict/preview", data=payload)

    assert response.status_code == 422
    assert response.json()["detail"] == detail


def test_malformed_manual_input_json_is_a_422(client):
    response = client.post(
        "/api/v1/predict/preview",
        data={"run_id": "1", "manual_input_data": "{not json"},
    )

    assert response.status_code == 422
    assert response.json()["detail"].startswith("Invalid manual_input_data JSON: ")
