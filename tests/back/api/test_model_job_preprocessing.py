import json

from fastapi.testclient import TestClient

from DashAI.back.dependencies.database.models import Dataset


def _create_session_with_binarizer(client: TestClient, dataset_id: int, name: str):
    return client.post(
        "/api/v1/model-session/",
        json={
            "dataset_id": dataset_id,
            "task_name": "TabularClassificationTask",
            "name": name,
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
                    "converter": "Binarizer",
                    "params": {"threshold": 3.0},
                    "scope": [{"kind": "raw", "name": "SepalLengthCm"}],
                },
            ],
            "input_column_refs": [{"kind": "group", "step": 0}],
        },
    )


def test_model_job_trains_using_a_converter_produced_group_column(
    client: TestClient, dataset_1: Dataset
):
    session_response = _create_session_with_binarizer(
        client, dataset_1.id, "preprocessing-training-session"
    )
    assert session_response.status_code == 201, session_response.text
    session_body = session_response.json()
    assert session_body["preprocessing_status"] == "ready"
    model_session_id = session_body["id"]

    run_response = client.post(
        "/api/v1/run/",
        json={
            "model_session_id": model_session_id,
            "model_name": "KNeighborsClassifier",
            "name": "PreprocessingRun",
            "parameters": {"n_neighbors": 3, "weights": "uniform", "algorithm": "auto"},
            "optimizer_name": "",
            "optimizer_parameters": {
                "n_trials": 10,
                "sampler": "TPESampler",
                "pruner": "None",
            },
            "goal_metric": "",
            "description": "Training with a group column from a converter",
            "plot_history_path": "path/to/history.png",
            "plot_slice_path": "path/to/slice.png",
            "plot_contour_path": "path/to/contour.png",
            "plot_importance_path": "path/to/importance.png",
        },
    )
    assert run_response.status_code == 201, run_response.text
    run_id = run_response.json()["id"]

    job_response = client.post(
        "/api/v1/job/",
        data={"job_type": "ModelJob", "kwargs": json.dumps({"run_id": run_id})},
    )
    assert job_response.status_code == 201, job_response.text
    job_id = job_response.json()["id"]

    job_status = client.get(f"/api/v1/job/status/{job_id}").json()
    assert job_status["status"] == "finished", job_status

    run_after = client.get(f"/api/v1/run/{run_id}").json()
    assert run_after["status"] == 3  # RunStatus.FINISHED
    assert run_after["run_path"] is not None

    client.delete(f"/api/v1/run/{run_id}")
    client.delete(f"/api/v1/model-session/{model_session_id}")


def test_model_job_trains_with_cross_validation_and_per_fold_preprocessing(
    client: TestClient, dataset_1: Dataset
):
    response = client.post(
        "/api/v1/model-session/",
        json={
            "dataset_id": dataset_1.id,
            "task_name": "TabularClassificationTask",
            "name": "preprocessing-cv-session",
            "input_columns": [],
            "output_columns": ["Species"],
            "train_metrics": [],
            "validation_metrics": [],
            "test_metrics": [],
            "evaluation_strategy": "CrossValidationEvaluationStrategy",
            "splits": json.dumps(
                {
                    "n_splits": 3,
                    "test_size": 0.0,
                    "is_random": True,
                    "has_changed": True,
                    "seed": 42,
                    "shuffle": True,
                    "stratify": False,
                    "splitter_name": "KFoldSplitter",
                }
            ),
            "preprocessing": [
                {
                    "converter": "Binarizer",
                    "params": {"threshold": 3.0},
                    "scope": [{"kind": "raw", "name": "SepalLengthCm"}],
                },
            ],
            "input_column_refs": [{"kind": "group", "step": 0}],
        },
    )
    assert response.status_code == 201, response.text
    session_body = response.json()
    assert session_body["preprocessing_status"] == "ready"
    model_session_id = session_body["id"]

    run_response = client.post(
        "/api/v1/run/",
        json={
            "model_session_id": model_session_id,
            "model_name": "KNeighborsClassifier",
            "name": "PreprocessingCVRun",
            "parameters": {"n_neighbors": 3, "weights": "uniform", "algorithm": "auto"},
            "optimizer_name": "",
            "optimizer_parameters": {
                "n_trials": 10,
                "sampler": "TPESampler",
                "pruner": "None",
            },
            "goal_metric": "",
            "description": "CV training with per-fold preprocessing",
            "plot_history_path": "path/to/history.png",
            "plot_slice_path": "path/to/slice.png",
            "plot_contour_path": "path/to/contour.png",
            "plot_importance_path": "path/to/importance.png",
        },
    )
    assert run_response.status_code == 201, run_response.text
    run_id = run_response.json()["id"]

    job_response = client.post(
        "/api/v1/job/",
        data={"job_type": "ModelJob", "kwargs": json.dumps({"run_id": run_id})},
    )
    assert job_response.status_code == 201, job_response.text
    job_id = job_response.json()["id"]

    job_status = client.get(f"/api/v1/job/status/{job_id}").json()
    assert job_status["status"] == "finished", job_status

    run_after = client.get(f"/api/v1/run/{run_id}").json()
    assert run_after["status"] == 3  # RunStatus.FINISHED

    client.delete(f"/api/v1/run/{run_id}")
    client.delete(f"/api/v1/model-session/{model_session_id}")
