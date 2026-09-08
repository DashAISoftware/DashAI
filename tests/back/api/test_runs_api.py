import json

import pytest
from fastapi.testclient import TestClient

from DashAI.back.dependencies.database.models import Dataset, Run, RunStatus


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


def test_delete_run_with_directory_run_path(
    client: TestClient, model_session_id: int, tmp_path
):
    """A FINISHED run whose run_path is a directory (Hugging Face-style
    models) must be deletable, not raise IsADirectoryError/PermissionError."""
    run_dir = tmp_path / "hf_style_run_dir"
    run_dir.mkdir()
    (run_dir / "config.json").write_text("{}")

    container = client.app.container
    session_factory = container["session_factory"]
    with session_factory() as db:
        run = Run(
            model_session_id=model_session_id,
            model_name="SomeHFModel",
            parameters={},
            optimizer_name="",
            optimizer_parameters={},
            goal_metric="",
            name="DirRun",
            status=RunStatus.FINISHED,
            run_path=str(run_dir),
        )
        db.add(run)
        db.commit()
        db.refresh(run)
        run_id = run.id

    response = client.delete(f"/api/v1/run/{run_id}")
    assert response.status_code == 204, response.text
    assert not run_dir.exists()


@pytest.mark.order(-1)
def test_delete_run(client: TestClient):
    # Delete all the runs in the db
    response = client.delete("/api/v1/run/1")
    assert response.status_code == 204
    response = client.delete("/api/v1/run/2")
    assert response.status_code == 204
