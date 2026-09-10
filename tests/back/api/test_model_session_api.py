import json

from fastapi.testclient import TestClient

from DashAI.back.dependencies.database.models import Dataset

SESSION_PARAMS = {
    "task_name": "TabularClassificationTask",
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
}


def test_delete_model_session(client: TestClient, dataset_1: Dataset) -> None:
    response = client.post(
        "/api/v1/model-session/",
        json={**SESSION_PARAMS, "dataset_id": dataset_1.id, "name": "delete_me"},
    )
    assert response.status_code == 201, response.text
    session_id = response.json()["id"]

    response = client.delete(f"/api/v1/model-session/{session_id}")
    assert response.status_code == 204, response.text

    response = client.get(f"/api/v1/model-session/{session_id}")
    assert response.status_code == 404, response.text

    response = client.delete("/api/v1/model-session/10000")
    assert response.status_code == 404, response.text


def test_bulk_delete_model_sessions(client: TestClient, dataset_1: Dataset) -> None:
    created_ids = []
    for name in ["bulk_delete_session_1", "bulk_delete_session_2"]:
        response = client.post(
            "/api/v1/model-session/",
            json={**SESSION_PARAMS, "dataset_id": dataset_1.id, "name": name},
        )
        assert response.status_code == 201, response.text
        created_ids.append(response.json()["id"])

    # A non-existent id mixed in should be skipped rather than failing the batch.
    response = client.request(
        "DELETE",
        "/api/v1/model-session/",
        json={"ids": [*created_ids, 999999]},
    )
    assert response.status_code == 204, response.text

    for session_id in created_ids:
        response = client.get(f"/api/v1/model-session/{session_id}")
        assert response.status_code == 404, response.text
