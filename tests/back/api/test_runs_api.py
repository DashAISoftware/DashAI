import json
import os

import pytest
from fastapi.testclient import TestClient

from DashAI.back.dependencies.database.models import Dataset


@pytest.fixture(scope="module", name="dataset_id")
def dataset_id(dataset_1: Dataset) -> int:
    """Get the dataset ID from the dataset_1 fixture."""
    return dataset_1.id


@pytest.fixture(scope="module", name="model_session_id")
def create_model_session(client: TestClient, dataset_id):
    """Create model session 1."""
    response = client.post(
        "/api/v1/model-session/",
        json={
            "dataset_id": dataset_id,
            "task_name": "TabularClassificationTask",
            "name": "Test Experiment",
            "input_columns": [
                "SepalLengthCm",
                "SepalWidthCm",
                "PetalLengthCm",
                "PetalWidthCm",
            ],
            "output_columns": ["Species"],
            "train_metrics": [],
            "validation_metrics": [],
            "test_metrics": [],
            "evaluation_strategy": "holdout",
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
        },
    )

    yield response.json()["id"]
    response = client.delete(f"/api/v1/model-session/{response.json()['id']}")
    assert response.status_code == 204, response.text


def test_create_run(client: TestClient, model_session_id: int):
    # create run using the model session
    response = client.post(
        "/api/v1/run/",
        json={
            "model_session_id": model_session_id,
            "model_name": "KNeighborsClassifier",
            "name": "Run1",
            "parameters": {"n_neighbors": 5, "weights": "uniform", "algorithm": "auto"},
            "optimizer_name": "OptunaOptimizer",
            "optimizer_parameters": {
                "n_trials": 10,
                "sampler": "TPESampler",
                "pruner": "None",
            },
            "goal_metric": "Accuracy",
            "description": "This is a test run",
            "plot_history_path": "path/to/history.png",  # Add missing fields
            "plot_slice_path": "path/to/slice.png",
            "plot_contour_path": "path/to/contour.png",
            "plot_importance_path": "path/to/importance.png",
        },
    )
    assert response.status_code == 201
    response = client.post(
        "/api/v1/run/",
        json={
            "model_session_id": model_session_id,
            "model_name": "KNeighborsClassifier",
            "name": "Run2",
            "parameters": {
                "n_neighbors": 3,
                "weights": "uniform",
                "algorithm": "kd_tree",
            },
            "optimizer_name": "OptunaOptimizer",
            "optimizer_parameters": {
                "n_trials": 10,
                "sampler": "TPESampler",
                "pruner": "None",
            },
            "goal_metric": "Accuracy",
            "description": "This is a test run",
            "plot_history_path": "path/to/history.png",  # Add missing fields
            "plot_slice_path": "path/to/slice.png",
            "plot_contour_path": "path/to/contour.png",
            "plot_importance_path": "path/to/importance.png",
        },
    )
    assert response.status_code == 201
    response = client.get("/api/v1/run/1")
    assert response.status_code == 200
    data = response.json()
    assert data["model_session_id"] == model_session_id
    assert data["model_name"] == "KNeighborsClassifier"
    assert data["name"] == "Run1"
    assert data["status"] == 0
    assert data["parameters"] == {
        "n_neighbors": 5,
        "weights": "uniform",
        "algorithm": "auto",
    }

    response = client.get("/api/v1/run/2")
    assert response.status_code == 200
    data = response.json()
    assert data["model_session_id"] == model_session_id
    assert data["model_name"] == "KNeighborsClassifier"
    assert data["name"] == "Run2"
    assert data["status"] == 0
    assert data["parameters"] == {
        "n_neighbors": 3,
        "weights": "uniform",
        "algorithm": "kd_tree",
    }


def test_create_run_with_cross_validation_strategy(client: TestClient, dataset_id: int):
    """A model session using CV should persist the CV split configuration."""
    create_session_response = client.post(
        "/api/v1/model-session/",
        json={
            "dataset_id": dataset_id,
            "task_name": "TabularClassificationTask",
            "name": "CV Session",
            "input_columns": [
                "SepalLengthCm",
                "SepalWidthCm",
                "PetalLengthCm",
                "PetalWidthCm",
            ],
            "output_columns": ["Species"],
            "train_metrics": [],
            "validation_metrics": [],
            "test_metrics": [],
            "evaluation_strategy": "CrossValidationEvaluationStrategy",
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
                    "splitType": "random",
                    "splitter_name": "KFoldSplitter",
                    "n_splits": 3,
                }
            ),
        },
    )
    assert create_session_response.status_code == 201, create_session_response.text

    session = create_session_response.json()
    response = client.get(f"/api/v1/model-session/{session['id']}")
    assert response.status_code == 200, response.text
    persisted_session = response.json()
    assert (
        persisted_session["evaluation_strategy"] == "CrossValidationEvaluationStrategy"
    )
    persisted_splits = json.loads(persisted_session["splits"])
    assert persisted_splits["splitter_name"] == "KFoldSplitter"
    assert persisted_splits["n_splits"] == 3

    create_run_response = client.post(
        "/api/v1/run/",
        json={
            "model_session_id": session["id"],
            "model_name": "KNeighborsClassifier",
            "name": "CV Run",
            "parameters": {"n_neighbors": 5, "weights": "uniform", "algorithm": "auto"},
            "optimizer_name": "OptunaOptimizer",
            "optimizer_parameters": {
                "n_trials": 10,
                "sampler": "TPESampler",
                "pruner": "None",
            },
            "goal_metric": "Accuracy",
            "description": "Cross-validation test run",
            "plot_history_path": "path/to/history.png",
            "plot_slice_path": "path/to/slice.png",
            "plot_contour_path": "path/to/contour.png",
            "plot_importance_path": "path/to/importance.png",
        },
    )
    assert create_run_response.status_code == 201, create_run_response.text
    created_run = create_run_response.json()
    assert created_run["name"] == "CV Run"
    assert created_run["model_session_id"] == session["id"]

    delete_session_response = client.delete(f"/api/v1/model-session/{session['id']}")
    assert delete_session_response.status_code == 204, delete_session_response.text


def test_create_model_session_persists_converters(client: TestClient, dataset_id: int):
    """`converters` set on a session must round-trip through create/get."""
    converters = [
        {
            "id": "conv_0",
            "converter": "StandardScaler",
            "params": {"with_mean": True},
            "input_scope": [{"kind": "column", "name": "SepalLengthCm"}],
        }
    ]
    expected_converters = [
        {
            "id": "conv_0",
            "converter": "StandardScaler",
            "params": {"with_mean": True},
            "input_scope": [
                {
                    "kind": "column",
                    "name": "SepalLengthCm",
                    "converter_id": None,
                    "slot": None,
                }
            ],
            "target_column": None,
        }
    ]
    response = client.post(
        "/api/v1/model-session/",
        json={
            "dataset_id": dataset_id,
            "task_name": "TabularClassificationTask",
            "name": "Converter Persistence Session",
            "input_columns": [
                "SepalLengthCm",
                "SepalWidthCm",
                "PetalLengthCm",
                "PetalWidthCm",
            ],
            "output_columns": ["Species"],
            "train_metrics": [],
            "validation_metrics": [],
            "test_metrics": [],
            "evaluation_strategy": "HoldoutEvaluationStrategy",
            "splits": json.dumps(
                {
                    "train": 0.6,
                    "test": 0.2,
                    "validation": 0.2,
                    "is_random": True,
                    "has_changed": True,
                    "seed": 42,
                    "shuffle": True,
                    "stratify": False,
                    "splitType": "random",
                    "splitter_name": "HoldoutSplitter",
                }
            ),
            "converters": converters,
        },
    )
    assert response.status_code == 201, response.text
    session = response.json()
    assert session["converters"] == expected_converters

    get_response = client.get(f"/api/v1/model-session/{session['id']}")
    assert get_response.status_code == 200, get_response.text
    persisted = get_response.json()
    assert persisted["converters"] == expected_converters
    # Creating a session with converters auto-enqueues preprocessing; in test
    # mode the job queue runs it synchronously, so it's already done by now.
    assert persisted["preprocessing_status"] == 3  # FINISHED
    assert persisted["preprocessed_path"] is not None

    delete_response = client.delete(f"/api/v1/model-session/{session['id']}")
    assert delete_response.status_code == 204, delete_response.text


def _create_and_run_session_with_converter(
    client: TestClient,
    dataset_id: int,
    evaluation_strategy: str,
    splits: dict,
    name: str,
):
    """Shared helper: create a session with a fit-dependent converter
    (StandardScaler), run it, and return (session, run_id, job_status).

    Uses real atom-shaped `input_columns`/`output_columns` (`{"kind":
    "column", "name": ...}`) and a converter entry with its own `"id"` and
    `input_scope` — the shape the real API/wizard actually produces since
    the group-atoms feature (`SessionConverterParams`/`ColumnAtom`), not
    the legacy plain-string/`"columns"` shape. StandardScaler doesn't
    rename or add columns, so the session's own final selection can stay
    literal `column` atoms throughout (no `group` atom needed here)."""
    create_session_response = client.post(
        "/api/v1/model-session/",
        json={
            "dataset_id": dataset_id,
            "task_name": "TabularClassificationTask",
            "name": name,
            "input_columns": [
                {"kind": "column", "name": "SepalLengthCm"},
                {"kind": "column", "name": "SepalWidthCm"},
                {"kind": "column", "name": "PetalLengthCm"},
                {"kind": "column", "name": "PetalWidthCm"},
            ],
            "output_columns": [{"kind": "column", "name": "Species"}],
            "train_metrics": [],
            "validation_metrics": [],
            "test_metrics": [],
            "evaluation_strategy": evaluation_strategy,
            "splits": json.dumps(splits),
            "converters": [
                {
                    "id": "conv_0",
                    "converter": "StandardScaler",
                    "params": {},
                    "input_scope": [],
                }
            ],
        },
    )
    assert create_session_response.status_code == 201, create_session_response.text
    session = create_session_response.json()

    create_run_response = client.post(
        "/api/v1/run/",
        json={
            "model_session_id": session["id"],
            "model_name": "KNeighborsClassifier",
            "name": f"{name} Run",
            "parameters": {
                "n_neighbors": 5,
                "weights": "uniform",
                "algorithm": "auto",
            },
            "optimizer_name": "",
            "optimizer_parameters": {
                "n_trials": 10,
                "sampler": "TPESampler",
                "pruner": "None",
            },
            "goal_metric": "",
            "description": f"{name} run",
            "plot_history_path": "path/to/history.png",
            "plot_slice_path": "path/to/slice.png",
            "plot_contour_path": "path/to/contour.png",
            "plot_importance_path": "path/to/importance.png",
        },
    )
    assert create_run_response.status_code == 201, create_run_response.text
    run_id = create_run_response.json()["id"]

    job_response = client.post(
        "/api/v1/job/",
        data={"job_type": "ModelJob", "kwargs": json.dumps({"run_id": run_id})},
    )
    assert job_response.status_code == 201, job_response.text
    job_id = job_response.json()["id"]

    status_response = client.get(f"/api/v1/job/status/{job_id}")
    assert status_response.status_code == 200, status_response.text

    return session, run_id, status_response.json()


def test_run_with_session_converter_holdout_finishes(
    client: TestClient, dataset_id: int
):
    """A holdout session with a fit-dependent converter should train and
    finish, confirming the fit-on-train mechanism is wired into ModelJob."""
    session, run_id, job_status = _create_and_run_session_with_converter(
        client,
        dataset_id,
        evaluation_strategy="HoldoutEvaluationStrategy",
        splits={
            "train": 0.6,
            "test": 0.2,
            "validation": 0.2,
            "is_random": True,
            "has_changed": True,
            "seed": 42,
            "shuffle": True,
            "stratify": False,
            "splitType": "random",
            "splitter_name": "HoldoutSplitter",
        },
        name="Converter Holdout Session",
    )
    assert job_status["status"] == "finished", job_status

    run_response = client.get(f"/api/v1/run/{run_id}")
    assert run_response.status_code == 200, run_response.text
    assert run_response.json()["status"] == 3

    # Predicting on brand-new (raw, unscaled) input must still work: the
    # StandardScaler fitted at training time is replayed on this input
    # before it reaches the model (see execution.transform_for_prediction).
    predict_response = client.post(
        "/api/v1/predict/preview",
        data={
            "run_id": str(run_id),
            "manual_input_data": json.dumps(
                [
                    {
                        "SepalLengthCm": 5.1,
                        "SepalWidthCm": 3.5,
                        "PetalLengthCm": 1.4,
                        "PetalWidthCm": 0.2,
                    }
                ]
            ),
        },
    )
    assert predict_response.status_code == 200, predict_response.text
    preview = predict_response.json()
    assert preview["columns"][-1] == "Species"
    assert len(preview["rows"]) == 1
    assert preview["rows"][0][:4] == [5.1, 3.5, 1.4, 0.2]  # preview shows raw input

    client.delete(f"/api/v1/model-session/{session['id']}")


def test_predict_with_session_converter_via_dataset(
    client: TestClient, dataset_id: int
):
    """End-to-end regression test for predict_job.py's real-column-name fix
    (`get_real_input_output_columns`): a session with converters and real
    atom-shaped `input_columns`/`output_columns` must be able to predict
    against a whole dataset (not just manual input), exercising
    `PredictJob.run()`'s own remaining call sites (`output_col`, the saved
    prediction dataset's `filtered_schema`) that
    `run_manual_prediction`/the holdout test above never touch, since they
    only ever call `_run_prediction_pipeline` directly."""
    session, run_id, job_status = _create_and_run_session_with_converter(
        client,
        dataset_id,
        evaluation_strategy="HoldoutEvaluationStrategy",
        splits={
            "train": 0.6,
            "test": 0.2,
            "validation": 0.2,
            "is_random": True,
            "has_changed": True,
            "seed": 42,
            "shuffle": True,
            "stratify": False,
            "splitType": "random",
            "splitter_name": "HoldoutSplitter",
        },
        name="Converter Dataset Predict Session",
    )
    assert job_status["status"] == "finished", job_status

    predict_response = client.post(
        "/api/v1/predict/",
        json={"run_id": run_id, "dataset_id": dataset_id},
    )
    assert predict_response.status_code == 200, predict_response.text
    prediction_id = predict_response.json()["id"]

    job_response = client.post(
        "/api/v1/job/",
        data={
            "job_type": "PredictJob",
            "kwargs": json.dumps({"prediction_id": prediction_id}),
        },
    )
    assert job_response.status_code == 201, job_response.text
    job_id = job_response.json()["id"]
    status_response = client.get(f"/api/v1/job/status/{job_id}")
    assert status_response.json()["status"] == "finished", status_response.json()

    prediction_response = client.get(
        "/api/v1/predict/", params={"prediction_id": prediction_id}
    )
    assert prediction_response.status_code == 200, prediction_response.text
    predictions = prediction_response.json()
    assert len(predictions) == 1
    assert predictions[0]["status"] == 3  # FINISHED

    client.delete(f"/api/v1/model-session/{session['id']}")


def test_run_with_session_converter_cross_validation_finishes(
    client: TestClient, dataset_id: int
):
    """A cross-validation session with a fit-dependent converter should
    train and finish: each fold (and the final full_dataset fold) fits its
    own converter independently, with no error along the way."""
    session, run_id, job_status = _create_and_run_session_with_converter(
        client,
        dataset_id,
        evaluation_strategy="CrossValidationEvaluationStrategy",
        splits={
            "train": 0.5,
            "test": 0.2,
            "validation": 0.3,
            "is_random": True,
            "has_changed": True,
            "seed": 42,
            "shuffle": False,
            "stratify": False,
            "splitType": "random",
            "splitter_name": "KFoldSplitter",
            "n_splits": 3,
        },
        name="Converter CV Session",
    )
    assert job_status["status"] == "finished", job_status

    run_response = client.get(f"/api/v1/run/{run_id}")
    assert run_response.status_code == 200, run_response.text
    assert run_response.json()["status"] == 3

    client.delete(f"/api/v1/model-session/{session['id']}")


def test_run_trains_with_group_atom_input_and_literal_output(
    client: TestClient, dataset_id: int
):
    """End-to-end regression test for the round-3 dataset_split_utils.py fix:
    a session whose `input_columns` references a converter's group output
    (the main use case the whole group-atoms feature exists for — e.g.
    "use everything PCA produced" as input features) must still resolve a
    REAL, literal `output_columns` at split time, not the placeholder.
    `load_dataset_and_splitter`'s placeholder-vs-real decision depends only
    on `output_columns`'s own resolvability now, never on `input_columns`'s
    — so the saved reference partition's `y` file must carry the session's
    real target values, and a Run must be able to actually train on it."""
    create_session_response = client.post(
        "/api/v1/model-session/",
        json={
            "dataset_id": dataset_id,
            "task_name": "TabularClassificationTask",
            "name": "Group Atom Input Real Output Session",
            "input_columns": [{"kind": "group", "converter_id": "conv_0", "slot": 0}],
            "output_columns": [{"kind": "column", "name": "Species"}],
            "train_metrics": [],
            "validation_metrics": [],
            "test_metrics": [],
            "evaluation_strategy": "HoldoutEvaluationStrategy",
            "splits": json.dumps(
                {
                    "train": 0.6,
                    "test": 0.2,
                    "validation": 0.2,
                    "is_random": True,
                    "has_changed": True,
                    "seed": 42,
                    "shuffle": True,
                    "stratify": False,
                    "splitType": "random",
                    "splitter_name": "HoldoutSplitter",
                }
            ),
            "converters": [
                {
                    "id": "conv_0",
                    "converter": "PCA",
                    "params": {"n_components": 2},
                    "input_scope": [
                        {"kind": "column", "name": "SepalLengthCm"},
                        {"kind": "column", "name": "SepalWidthCm"},
                        {"kind": "column", "name": "PetalLengthCm"},
                        {"kind": "column", "name": "PetalWidthCm"},
                    ],
                }
            ],
        },
    )
    assert create_session_response.status_code == 201, create_session_response.text
    session = create_session_response.json()
    assert session["preprocessing_status"] == 3, session  # FINISHED

    # The saved reference partition's `y` file must carry the REAL output
    # values, not the placeholder — the actual regression this test guards.
    from DashAI.back.dataloaders.classes.dashai_dataset import load_dataset
    from DashAI.back.dependencies.database.models import ModelSession

    session_factory = client.app.container["session_factory"]
    with session_factory() as db:
        model_session = db.get(ModelSession, session["id"])
        preprocessed_path = model_session.preprocessed_path

    x_train = load_dataset(os.path.join(preprocessed_path, "train", "x"))
    y_train = load_dataset(os.path.join(preprocessed_path, "train", "y"))
    assert set(x_train.column_names) == {"pca0", "pca1"}
    assert y_train.column_names == ["Species"]
    assert set(y_train["Species"]) <= {
        "Iris-setosa",
        "Iris-versicolor",
        "Iris-virginica",
    }

    create_run_response = client.post(
        "/api/v1/run/",
        json={
            "model_session_id": session["id"],
            "model_name": "KNeighborsClassifier",
            "name": "Group Atom Input Run",
            "parameters": {
                "n_neighbors": 5,
                "weights": "uniform",
                "algorithm": "auto",
            },
            "optimizer_name": "",
            "optimizer_parameters": {
                "n_trials": 10,
                "sampler": "TPESampler",
                "pruner": "None",
            },
            "goal_metric": "",
            "description": "Group atom input run",
            "plot_history_path": "path/to/history.png",
            "plot_slice_path": "path/to/slice.png",
            "plot_contour_path": "path/to/contour.png",
            "plot_importance_path": "path/to/importance.png",
        },
    )
    assert create_run_response.status_code == 201, create_run_response.text
    run_id = create_run_response.json()["id"]

    job_response = client.post(
        "/api/v1/job/",
        data={"job_type": "ModelJob", "kwargs": json.dumps({"run_id": run_id})},
    )
    assert job_response.status_code == 201, job_response.text
    job_id = job_response.json()["id"]
    status_response = client.get(f"/api/v1/job/status/{job_id}")
    assert status_response.json()["status"] == "finished", status_response.json()

    run_response = client.get(f"/api/v1/run/{run_id}")
    assert run_response.status_code == 200, run_response.text
    assert run_response.json()["status"] == 3  # FINISHED

    client.delete(f"/api/v1/model-session/{session['id']}")


def test_predict_with_input_column_added_by_converter(
    client: TestClient, dataset_id: int
):
    """Regression test: manual prediction input is always in the *raw*
    dataset's schema — predict_job.py replays a session's fitted converters
    on it before the model sees it (same principle as predicting with raw,
    unscaled StandardScaler input in the holdout test above). Using PCA to
    turn the 4 raw numeric columns into `pca0`/`pca1` used to break this two
    different ways: a `KeyError` selecting `pca0`/`pca1` straight from the
    raw-schema loaded dataset (selection ran before the fitted PCA replay),
    and, before that, "Column 'pca0' not found in training dataset" from
    `process_manual_input` validating manual input against the raw
    dataset's own columns."""
    pca_config = [
        {
            "id": "conv_0",
            "converter": "PCA",
            "params": {"n_components": 2},
            "input_scope": [
                {"kind": "column", "name": name}
                for name in [
                    "SepalLengthCm",
                    "SepalWidthCm",
                    "PetalLengthCm",
                    "PetalWidthCm",
                ]
            ],
        }
    ]
    # The session's own final `input_columns` is the PCA group atom itself
    # (what the wizard's Columns step actually offers once preprocessing has
    # run: the current, already-transformed columns) — `SessionPreprocessingJob`
    # resolves it to the real `pca0`/`pca1` names via `resolve_final_columns`.
    # The converter's own `input_scope` above (the 4 raw columns) is what
    # PCA fits on; the two are resolved independently.
    create_session_response = client.post(
        "/api/v1/model-session/",
        json={
            "dataset_id": dataset_id,
            "task_name": "TabularClassificationTask",
            "name": "PCA Predict Session",
            "input_columns": [{"kind": "group", "converter_id": "conv_0", "slot": 0}],
            "output_columns": ["Species"],
            "train_metrics": [],
            "validation_metrics": [],
            "test_metrics": [],
            "evaluation_strategy": "HoldoutEvaluationStrategy",
            "splits": json.dumps(
                {
                    "train": 0.6,
                    "test": 0.2,
                    "validation": 0.2,
                    "is_random": True,
                    "has_changed": True,
                    "seed": 42,
                    "shuffle": True,
                    "stratify": False,
                    "splitType": "random",
                    "splitter_name": "HoldoutSplitter",
                }
            ),
            "converters": pca_config,
        },
    )
    assert create_session_response.status_code == 201, create_session_response.text
    session = create_session_response.json()
    assert session["preprocessing_status"] == 3, session  # FINISHED

    create_run_response = client.post(
        "/api/v1/run/",
        json={
            "model_session_id": session["id"],
            "model_name": "KNeighborsClassifier",
            "name": "PCA Predict Run",
            "parameters": {
                "n_neighbors": 5,
                "weights": "uniform",
                "algorithm": "auto",
            },
            "optimizer_name": "",
            "optimizer_parameters": {
                "n_trials": 10,
                "sampler": "TPESampler",
                "pruner": "None",
            },
            "goal_metric": "",
            "description": "PCA predict run",
            "plot_history_path": "path/to/history.png",
            "plot_slice_path": "path/to/slice.png",
            "plot_contour_path": "path/to/contour.png",
            "plot_importance_path": "path/to/importance.png",
        },
    )
    assert create_run_response.status_code == 201, create_run_response.text
    run_id = create_run_response.json()["id"]

    job_response = client.post(
        "/api/v1/job/",
        data={"job_type": "ModelJob", "kwargs": json.dumps({"run_id": run_id})},
    )
    assert job_response.status_code == 201, job_response.text
    job_id = job_response.json()["id"]
    status_response = client.get(f"/api/v1/job/status/{job_id}")
    assert status_response.json()["status"] == "finished", status_response.json()

    # Manual input matches the *raw* dataset's schema — the 4 original
    # numeric columns — never `pca0`/`pca1`.
    predict_response = client.post(
        "/api/v1/predict/preview",
        data={
            "run_id": str(run_id),
            "manual_input_data": json.dumps(
                [
                    {
                        "SepalLengthCm": 5.1,
                        "SepalWidthCm": 3.5,
                        "PetalLengthCm": 1.4,
                        "PetalWidthCm": 0.2,
                    }
                ]
            ),
        },
    )
    assert predict_response.status_code == 200, predict_response.text
    preview = predict_response.json()
    # Preview shows the raw schema the user actually entered, never the
    # converter-produced pca0/pca1.
    assert "pca0" not in preview["columns"]
    assert set(preview["columns"]) == {
        "SepalLengthCm",
        "SepalWidthCm",
        "PetalLengthCm",
        "PetalWidthCm",
        "Species",
    }
    assert len(preview["rows"]) == 1

    # Regression check: the dataset-picker's compatibility filter must use
    # the same raw schema — comparing candidate datasets against
    # `model_session.input_columns` (`pca0`/`pca1`) meant no real dataset
    # (this one included) could ever match, leaving the picker empty.
    filter_response = client.get(
        "/api/v1/predict/filter_datasets",
        params={"run_id": run_id},
    )
    assert filter_response.status_code == 200, filter_response.text
    assert dataset_id in filter_response.json()["valid_dataset_ids"]

    client.delete(f"/api/v1/model-session/{session['id']}")


def test_get_run(client: TestClient):
    response = client.get("/api/v1/run/1")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Run1"
    response = client.get("/api/v1/run/2")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Run2"


def test_get_all_runs(client: TestClient, model_session_id: int):
    response = client.get(f"/api/v1/run/?model_session_id={model_session_id}")
    assert response.status_code == 200
    data = response.json()
    assert data[0]["model_session_id"] == model_session_id
    assert data[1]["model_session_id"] == model_session_id


def test_get_wrong_run(client: TestClient):
    # Try to retrieve a non-existent run an get an error
    response = client.get("/api/v1/run/31415")
    assert response.status_code == 404
    assert response.text == '{"detail":"Run not found"}'


def test_get_wrong_runs(client: TestClient):
    response = client.get("/api/v1/run/?model_session_id=31415")
    assert response.status_code == 404


def test_modify_run(client: TestClient):
    response = client.patch(
        "/api/v1/run/1",
        json={
            "parameters": {
                "n_neighbors": 3,
                "weights": "uniform",
                "algorithm": "kd_tree",
            },
            "run_name": "RunA",
        },
    )
    assert response.status_code == 200

    response = client.get("/api/v1/run/1")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "RunA"
    assert data["status"] == 0
    assert data["parameters"] == {
        "n_neighbors": 3,
        "weights": "uniform",
        "algorithm": "kd_tree",
    }
    assert data["created"] != data["last_modified"]


def test_modify_run_model(client: TestClient):
    # Send an empty request body (no valid parameters)
    # This should return 304 since no parameters are being updated
    response = client.patch(
        "/api/v1/run/2",
        json={},
    )
    assert response.status_code == 304


@pytest.mark.order(-1)
def test_delete_run(client: TestClient):
    # Delete all the runs in the db
    response = client.delete("/api/v1/run/1")
    assert response.status_code == 204
    response = client.delete("/api/v1/run/2")
    assert response.status_code == 204
