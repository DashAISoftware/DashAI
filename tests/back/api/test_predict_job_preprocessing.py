"""``PredictJob`` and the preview against a session that preprocesses.

``test_predict_preprocessing.py`` covers the preview through a run trained by
``ModelJob``. The job itself, on a whole dataset, on one partition of it and on
hand-typed rows, is covered here, and the run is fitted by hand on the column
the persisted preprocessor derives. What is under test is the prediction path,
not the training one: a model trained on ``bin_SepalLengthCm`` can only be
predicted with when the rows it is handed have been through the same fitted
Binarizer, and the raw iris rows never carry that column.

Every test compares what the job saved with the labels the model gives when
handed rows transformed by the fitted preprocessor directly, so it can tell a
prediction made on the derived column from one that was not.

Lives under ``tests/back/api`` to reuse the ``client`` and ``dataset_1``
fixtures from this package's ``conftest.py``.
"""

import json
import random
from pathlib import Path

import pytest
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
from DashAI.back.job.predict_job import PredictJob
from DashAI.back.preprocessing.session_preprocessor import load_final_preprocessor

RAW_INPUT_COLUMNS = [
    "SepalLengthCm",
    "SepalWidthCm",
    "PetalLengthCm",
    "PetalWidthCm",
]
SCOPED_COLUMN = "SepalLengthCm"
DERIVED_COLUMN = "bin_SepalLengthCm"
OUTPUT_COLUMN = "Species"
IRIS_ROWS = 150
THRESHOLD = 3.0
MODEL_PARAMETERS = {"n_neighbors": 3, "weights": "uniform", "algorithm": "auto"}


@pytest.fixture(scope="module", name="preprocessing_session")
def create_preprocessing_session(client: TestClient, dataset_1: Dataset):
    """A session whose one input column is produced by a Binarizer.

    Creating it runs ``PreprocessingJob`` synchronously: the fitted
    preprocessor lands in ``final.pkl`` under the session's artifacts path and
    ``input_columns`` is rewritten with the name the converter produced.
    """
    response = client.post(
        "/api/v1/model-session/",
        json={
            "dataset_id": dataset_1.id,
            "task_name": "TabularClassificationTask",
            "name": "predict-job-preprocessing-session",
            "input_columns": [],
            "output_columns": [OUTPUT_COLUMN],
            "train_metrics": [],
            "validation_metrics": [],
            "test_metrics": [],
            "evaluation_strategy": "HoldoutEvaluationStrategy",
            "splits": json.dumps(
                {
                    "train": 0.5,
                    "test": 0.2,
                    "validation": 0.3,
                    "is_random": True,
                    "has_changed": True,
                    "seed": 42,
                    "shuffle": True,
                    "stratify": False,
                }
            ),
            "preprocessing": [
                {
                    "converter": "Binarizer",
                    "params": {"threshold": THRESHOLD},
                    "scope": [{"kind": "raw", "name": SCOPED_COLUMN}],
                },
            ],
            "input_column_refs": [{"kind": "group", "step": 0}],
        },
    )
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["preprocessing_status"] == "ready", body

    session_factory = client.app.container["session_factory"]
    with session_factory() as db:
        row = db.get(ModelSession, body["id"])
        assert row.input_columns == [DERIVED_COLUMN]
        assert row.preprocessing_artifacts_path
        db.expunge(row)
        return row


@pytest.fixture(scope="module", name="fitted")
def fit_a_run_by_hand(
    client: TestClient,
    dataset_1: Dataset,
    preprocessing_session: ModelSession,
    tmp_path_factory,
):
    """A run trained on the derived column, saved where its ``Run`` row points.

    Fitted the way a training run would be, on the training partition of the
    rows the persisted preprocessor transforms, and handed back together with
    what fitted it so a test can compute the labels the model gives on rows it
    transforms itself.
    """
    registry = client.app.container["component_registry"]
    session_factory = client.app.container["session_factory"]

    raw = load_dataset(str(Path(dataset_1.file_path) / "dataset"))
    preprocessor = load_final_preprocessor(preprocessing_session)
    task = registry["TabularClassificationTask"]["class"]()
    transformed = task.prepare_for_task(
        preprocessor.transform_dataset(raw), [DERIVED_COLUMN], [OUTPUT_COLUMN]
    )
    assert DERIVED_COLUMN in transformed.column_names
    assert DERIVED_COLUMN not in raw.column_names

    rows = list(range(IRIS_ROWS))
    random.Random(875).shuffle(rows)
    split_indexes = {
        "train_indexes": sorted(rows[:75]),
        "test_indexes": sorted(rows[75:105]),
        "val_indexes": sorted(rows[105:]),
    }

    model = registry["KNeighborsClassifier"]["class"](**MODEL_PARAMETERS)
    train = transformed.select(split_indexes["train_indexes"])
    model.train(
        train.select_columns([DERIVED_COLUMN]), train.select_columns([OUTPUT_COLUMN])
    )
    model_path = tmp_path_factory.mktemp("predict-job-preprocessing") / "model"
    model.save(str(model_path))

    with session_factory() as db:
        run = Run(
            model_session_id=preprocessing_session.id,
            model_name="KNeighborsClassifier",
            parameters=MODEL_PARAMETERS,
            optimizer_name="OptunaOptimizer",
            optimizer_parameters={
                "n_trials": 1,
                "sampler": "TPESampler",
                "pruner": "None",
            },
            name="PredictJobPreprocessingRun",
            goal_metric="Accuracy",
            run_path=str(model_path),
            split_indexes=json.dumps(split_indexes),
        )
        run.set_status_as_finished()
        db.add(run)
        db.commit()
        db.refresh(run)
        run_id = run.id

    return {
        "run_id": run_id,
        "model": model,
        "task": task,
        "preprocessor": preprocessor,
        "raw": raw,
        "split_indexes": split_indexes,
    }


def _create_prediction(client, run_id, dataset_id=None, split=None):
    response = client.post(
        "/api/v1/predict/",
        json={"run_id": run_id, "dataset_id": dataset_id, "split": split},
    )
    assert response.status_code == 200, response.text
    return response.json()["id"]


def _stored_prediction(client, prediction_id):
    session_factory = client.app.container["session_factory"]
    with session_factory() as db:
        prediction = db.get(Prediction, prediction_id)
        return {
            "status": prediction.status,
            "results_path": prediction.results_path,
        }


def _saved_dataset(client, prediction_id):
    stored = _stored_prediction(client, prediction_id)
    assert stored["status"] == PredictionStatus.FINISHED
    return load_dataset(str(Path(stored["results_path"]) / "dataset"))


def _expected_labels(fitted, rows):
    """The labels the model gives rows it is handed already transformed.

    The same steps the job has to take, done by hand: transform with the
    persisted preprocessor, select the derived column, decode against the
    training dataset. A prediction made on anything else disagrees with it.
    """
    import numpy as np

    transformed = fitted["preprocessor"].transform_dataset(rows)
    proba = fitted["model"].predict(transformed.select_columns([DERIVED_COLUMN]))
    decoded = fitted["task"].process_predictions(
        fitted["raw"], np.array(proba), OUTPUT_COLUMN
    )
    return [str(label) for label in decoded]


def test_a_prediction_on_a_dataset_applies_the_persisted_preprocessor(
    client, dataset_1, fitted
):
    """The whole dataset: every row goes through the fitted Binarizer before
    the model sees it, and what is saved is the raw rows plus the prediction.
    The derived column never reaches disk."""
    prediction_id = _create_prediction(client, fitted["run_id"], dataset_1.id)

    PredictJob(prediction_id=prediction_id).run()

    saved = _saved_dataset(client, prediction_id)
    assert saved.column_names == RAW_INPUT_COLUMNS + [OUTPUT_COLUMN]
    assert len(saved) == IRIS_ROWS
    assert saved[OUTPUT_COLUMN] == _expected_labels(fitted, fitted["raw"])


def test_a_prediction_on_a_partition_transforms_exactly_its_rows(
    client, dataset_1, fitted
):
    """The partition is narrowed first and transformed second, so the saved
    prediction covers the rows of that partition and no others, raw."""
    prediction_id = _create_prediction(
        client, fitted["run_id"], dataset_1.id, split="test"
    )

    PredictJob(prediction_id=prediction_id).run()

    test_indexes = fitted["split_indexes"]["test_indexes"]
    partition = fitted["raw"].select(test_indexes)
    saved = _saved_dataset(client, prediction_id)
    assert saved.column_names == RAW_INPUT_COLUMNS + [OUTPUT_COLUMN]
    assert len(saved) == len(test_indexes)
    assert (
        saved.select_columns(RAW_INPUT_COLUMNS).to_dict()
        == partition.select_columns(RAW_INPUT_COLUMNS).to_dict()
    )
    assert saved[OUTPUT_COLUMN] == _expected_labels(fitted, partition)


def test_a_manual_prediction_through_the_job_applies_the_persisted_preprocessor(
    client, dataset_1, fitted
):
    """Hand-typed rows carry the raw feature the converter scoped on and
    nothing else; the job transforms them the same way it does a dataset."""
    rows = [{SCOPED_COLUMN: THRESHOLD}, {SCOPED_COLUMN: THRESHOLD + 4.0}]
    prediction_id = _create_prediction(client, fitted["run_id"])

    PredictJob(prediction_id=prediction_id, manual_input_data=rows).run()

    typed_rows = fitted["task"].process_manual_input(
        rows, str(Path(dataset_1.file_path) / "dataset")
    )
    saved = _saved_dataset(client, prediction_id)
    assert saved.column_names == [SCOPED_COLUMN, OUTPUT_COLUMN]
    assert saved[SCOPED_COLUMN] == [THRESHOLD, THRESHOLD + 4.0]
    assert saved[OUTPUT_COLUMN] == _expected_labels(fitted, typed_rows)


def test_the_preview_shows_the_column_the_model_saw(client, dataset_1, fitted):
    """Unlike the job, the preview answers with the model input: the session's
    input columns are the derived ones, so those are what the rows carry."""
    rows = [{SCOPED_COLUMN: THRESHOLD}, {SCOPED_COLUMN: THRESHOLD + 4.0}]

    response = client.post(
        "/api/v1/predict/preview",
        data={
            "run_id": str(fitted["run_id"]),
            "manual_input_data": json.dumps(rows),
        },
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["columns"] == [DERIVED_COLUMN, OUTPUT_COLUMN]
    # A Binarizer at the threshold: at it is 0, above it is 1.
    assert [row[0] for row in body["rows"]] == [0, 1]
    typed_rows = fitted["task"].process_manual_input(
        rows, str(Path(dataset_1.file_path) / "dataset")
    )
    assert [row[1] for row in body["rows"]] == _expected_labels(fitted, typed_rows)


@pytest.fixture(name="session_without_artifacts")
def forget_the_fitted_artifacts(client: TestClient, fitted):
    """The fitted session with its artifacts path nulled, restored afterwards.

    That is the state of a session whose preprocessing is still pending or
    failed: steps declared, nothing fitted. The fixture is module scoped, so
    the path goes back in a ``finally`` for the tests that run after this one.
    """
    session_factory = client.app.container["session_factory"]
    with session_factory() as db:
        run = db.get(Run, fitted["run_id"])
        model_session = db.get(ModelSession, run.model_session_id)
        artifacts_path = model_session.preprocessing_artifacts_path
        model_session.preprocessing_artifacts_path = None
        db.commit()
    try:
        yield
    finally:
        with session_factory() as db:
            run = db.get(Run, fitted["run_id"])
            model_session = db.get(ModelSession, run.model_session_id)
            model_session.preprocessing_artifacts_path = artifacts_path
            db.commit()


def test_a_session_with_steps_but_no_artifacts_refuses_to_predict(
    client, dataset_1, fitted, session_without_artifacts
):
    """Steps declared and nothing fitted: the rows must not be predicted raw.

    The refusal carries its own message rather than the generic "Model
    prediction failed", and the prediction ends in error.
    """
    prediction_id = _create_prediction(client, fitted["run_id"], dataset_1.id)

    with pytest.raises(JobError, match="no fitted preprocessor"):
        PredictJob(prediction_id=prediction_id).run()

    assert _stored_prediction(client, prediction_id)["status"] == PredictionStatus.ERROR


def test_the_preview_answers_409_while_the_session_has_no_artifacts(
    client, fitted, session_without_artifacts
):
    response = client.post(
        "/api/v1/predict/preview",
        data={
            "run_id": str(fitted["run_id"]),
            "manual_input_data": json.dumps([{SCOPED_COLUMN: THRESHOLD}]),
        },
    )

    assert response.status_code == 409, response.text
    assert "no fitted preprocessor" in response.json()["detail"]
