import json

from fastapi.testclient import TestClient

from DashAI.back.dependencies.database.models import Dataset


def _create_and_train_session_with_binarizer(client: TestClient, dataset_id: int):
    session_response = client.post(
        "/api/v1/model-session/",
        json={
            "dataset_id": dataset_id,
            "task_name": "TabularClassificationTask",
            "name": "predict-preprocessing-session",
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
    assert session_response.status_code == 201, session_response.text
    model_session_id = session_response.json()["id"]

    run_response = client.post(
        "/api/v1/run/",
        json={
            "model_session_id": model_session_id,
            "model_name": "KNeighborsClassifier",
            "name": "PredictPreprocessingRun",
            "parameters": {"n_neighbors": 3, "weights": "uniform", "algorithm": "auto"},
            "optimizer_name": "",
            "optimizer_parameters": {
                "n_trials": 10,
                "sampler": "TPESampler",
                "pruner": "None",
            },
            "goal_metric": "",
            "description": "Training for prediction preprocessing test",
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

    return model_session_id, run_id


def test_manual_prediction_applies_the_persisted_preprocessor(
    client: TestClient, dataset_1: Dataset
):
    """A manual prediction row carries only the raw feature the converter
    scoped on ("SepalLengthCm"), never the converter-produced column
    ("bin_SepalLengthCm") the model was actually trained on. Predicting
    must apply the persisted fitted Binarizer to the raw row before handing
    it to the model, without ever re-fitting on it.
    """
    model_session_id, run_id = _create_and_train_session_with_binarizer(
        client, dataset_1.id
    )

    response = client.post(
        "/api/v1/predict/preview",
        data={
            "run_id": str(run_id),
            "manual_input_data": json.dumps([{"SepalLengthCm": 3.0}]),
        },
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert "columns" in body
    assert len(body["rows"]) == 1

    client.delete(f"/api/v1/model-session/{model_session_id}")
