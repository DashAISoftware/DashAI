import json

from fastapi.testclient import TestClient

from DashAI.back.dependencies.database.models import Dataset, ModelSession


def test_run_creation_is_rejected_while_preprocessing_is_pending(
    client: TestClient, dataset_1: Dataset
):
    session_response = client.post(
        "/api/v1/model-session/",
        json={
            "dataset_id": dataset_1.id,
            "task_name": "TabularClassificationTask",
            "name": "pending-guard-session",
            "input_columns": ["SepalLengthCm"],
            "output_columns": ["Species"],
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
        },
    )
    assert session_response.status_code == 201, session_response.text
    model_session_id = session_response.json()["id"]

    # The test client runs the job queue in immediate mode, so a session
    # never actually stays "pending" long enough to observe over the API.
    # Force it here to exercise the guard the way production would hit it
    # while PreprocessingJob is still running asynchronously.
    container = client.app.container
    session_factory = container["session_factory"]
    with session_factory() as db:
        model_session = db.get(ModelSession, model_session_id)
        model_session.preprocessing_status = "pending"
        db.commit()

    response = client.post(
        "/api/v1/run/",
        json={
            "model_session_id": model_session_id,
            "model_name": "KNeighborsClassifier",
            "name": "ShouldBeBlocked",
            "parameters": {"n_neighbors": 3, "weights": "uniform", "algorithm": "auto"},
            "optimizer_name": "",
            "optimizer_parameters": {
                "n_trials": 10,
                "sampler": "TPESampler",
                "pruner": "None",
            },
            "goal_metric": "",
            "description": "Should be rejected",
            "plot_history_path": "path/to/history.png",
            "plot_slice_path": "path/to/slice.png",
            "plot_contour_path": "path/to/contour.png",
            "plot_importance_path": "path/to/importance.png",
        },
    )
    assert response.status_code == 409, response.text

    client.delete(f"/api/v1/model-session/{model_session_id}")


def test_run_creation_surfaces_the_preprocessing_error_when_failed(
    client: TestClient, dataset_1: Dataset
):
    session_response = client.post(
        "/api/v1/model-session/",
        json={
            "dataset_id": dataset_1.id,
            "task_name": "TabularClassificationTask",
            "name": "failed-guard-session",
            "input_columns": [],
            "output_columns": ["Species"],
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
                    # A chain the structure estimate accepts but the data
                    # breaks: SepalLengthCm holds decimals (e.g. 5.1), which
                    # cannot be cast to Integer, so PreprocessingJob fails.
                    "converter": "TypeCast",
                    "params": {"new_type": "Integer", "on_error": "raise"},
                    "scope": [{"kind": "raw", "name": "SepalLengthCm"}],
                },
            ],
            "input_column_refs": [{"kind": "raw", "name": "SepalLengthCm"}],
        },
    )
    assert session_response.status_code == 201, session_response.text
    body = session_response.json()
    assert body["preprocessing_status"] == "failed"
    model_session_id = body["id"]

    response = client.post(
        "/api/v1/run/",
        json={
            "model_session_id": model_session_id,
            "model_name": "KNeighborsClassifier",
            "name": "ShouldBeBlocked",
            "parameters": {"n_neighbors": 3, "weights": "uniform", "algorithm": "auto"},
            "optimizer_name": "",
            "optimizer_parameters": {
                "n_trials": 10,
                "sampler": "TPESampler",
                "pruner": "None",
            },
            "goal_metric": "",
            "description": "Should be rejected",
            "plot_history_path": "path/to/history.png",
            "plot_slice_path": "path/to/slice.png",
            "plot_contour_path": "path/to/contour.png",
            "plot_importance_path": "path/to/importance.png",
        },
    )
    assert response.status_code == 409, response.text
    assert "preprocessing" in response.json()["detail"].lower()

    client.delete(f"/api/v1/model-session/{model_session_id}")
