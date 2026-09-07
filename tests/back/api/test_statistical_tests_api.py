import pytest
from fastapi.testclient import TestClient

from DashAI.back.dependencies.database.models import Dataset, ModelSession


@pytest.fixture(name="model_session_id")
def create_model_session_id(client: TestClient, dataset_1: Dataset):
    """Create a model session that can own saved statistical test rows."""
    session_factory = client.app.container["session_factory"]

    with session_factory() as db:
        model_session = ModelSession(
            dataset_id=dataset_1.id,
            name="statistical-tests-session",
            task_name="TabularClassificationTask",
            input_columns=["SepalLengthCm", "SepalWidthCm"],
            output_columns=["Species"],
            train_metrics=[],
            validation_metrics=[],
            test_metrics=[],
            evaluation_strategy="holdout",
            splits={
                "train": 0.8,
                "test": 0.2,
                "validation": 0.0,
                "seed": 42,
                "shuffle": True,
                "stratify": False,
            },
        )
        db.add(model_session)
        db.commit()
        db.refresh(model_session)
        yield model_session.id
        db.delete(model_session)
        db.commit()


def test_run_statistical_test_returns_result(client: TestClient):
    """The endpoint should run a supported statistical test and return metadata."""
    response = client.post(
        "/api/v1/statistical-tests/run",
        json={
            "test_name": "PairedTTest",
            "metric_name": "accuracy",
            "metric_split": "test",
            "run_ids": [1, 2],
            "run_names": {"1": "RunA", "2": "RunB"},
            "fold_metrics": {
                "1": [0.7, 0.8, 0.9, 0.95],
                "2": [0.2, 0.3, 0.4, 0.4],
            },
            "alpha": 0.05,
            "params": {"alternative": "two-sided"},
        },
    )

    assert response.status_code == 200, response.text
    data = response.json()
    assert data["test_name"] == "PairedTTest"
    assert data["significant"] is True
    assert data["p_value"] is not None
    assert data["statistic"] is not None
    assert data["details"]["scores"] == {
        "1": [0.7, 0.8, 0.9, 0.95],
        "2": [0.2, 0.3, 0.4, 0.4],
    }


def test_run_statistical_test_rejects_empty_fold_metrics(client: TestClient):
    """The endpoint should reject empty fold_metrics payloads."""
    response = client.post(
        "/api/v1/statistical-tests/run",
        json={
            "test_name": "PairedTTest",
            "metric_name": "accuracy",
            "metric_split": "test",
            "run_ids": [1, 2],
            "run_names": {"1": "RunA", "2": "RunB"},
            "fold_metrics": {},
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "fold_metrics cannot be empty"


def test_run_statistical_test_rejects_unknown_test(client: TestClient):
    """The endpoint should reject unknown statistical test names."""
    response = client.post(
        "/api/v1/statistical-tests/run",
        json={
            "test_name": "UnknownTest",
            "metric_name": "accuracy",
            "metric_split": "test",
            "run_ids": [1, 2],
            "run_names": {"1": "RunA", "2": "RunB"},
            "fold_metrics": {"1": [1.0, 2.0], "2": [2.0, 1.0]},
        },
    )

    assert response.status_code == 400
    assert "Unknown statistical test" in response.json()["detail"]


def test_save_list_and_delete_statistical_tests(
    client: TestClient, model_session_id: int
):
    """Saved results should be stored, listed, and removed through the API."""
    payload = [
        {
            "test_name": "PairedTTest",
            "metric_name": "accuracy",
            "metric_split": "test",
            "alpha": 0.05,
            "significant": True,
            "name": "First result",
            "description": "Saved from the API",
            "run_ids": [1, 2],
            "run_names": {"1": "RunA", "2": "RunB"},
            "statistic": 2.75,
            "p_value": 0.01,
            "interpretation": "Significant",
            "params": {"alternative": "two-sided"},
            "details": {"folds": 4},
            "posthoc": [],
            "model_session_id": model_session_id,
        },
        {
            "test_name": "PairedTTest",
            "metric_name": "accuracy",
            "metric_split": "validation",
            "alpha": 0.05,
            "significant": False,
            "name": "Second result",
            "description": "Saved from the API",
            "run_ids": [1, 2],
            "run_names": {"1": "RunA", "2": "RunB"},
            "statistic": 0.5,
            "p_value": 0.6,
            "interpretation": "Not significant",
            "params": {"alternative": "two-sided"},
            "details": {"folds": 4},
            "posthoc": [],
            "model_session_id": model_session_id,
        },
    ]

    save_response = client.post(
        "/api/v1/statistical-tests/save",
        json=payload,
    )
    assert save_response.status_code == 201, save_response.text
    saved_items = save_response.json()
    assert len(saved_items) == 2
    assert saved_items[0]["model_session_id"] == model_session_id
    assert saved_items[1]["model_session_id"] == model_session_id
    assert saved_items[0]["group_id"] == saved_items[1]["group_id"]

    list_response = client.get(
        f"/api/v1/statistical-tests/saved?model_session_id={model_session_id}"
    )
    assert list_response.status_code == 200, list_response.text
    listed_items = list_response.json()
    assert len(listed_items) >= 2
    assert any(item["name"] == "First result" for item in listed_items)

    group_id = saved_items[0]["group_id"]
    filtered_response = client.get(
        f"/api/v1/statistical-tests/saved?group_id={group_id}"
    )
    assert filtered_response.status_code == 200, filtered_response.text
    filtered_items = filtered_response.json()
    assert len(filtered_items) == 2

    delete_response = client.delete(
        f"/api/v1/statistical-tests/saved/{saved_items[0]['id']}"
    )
    assert delete_response.status_code == 200, delete_response.text
    assert delete_response.json() == {
        "deleted": True,
        "id": saved_items[0]["id"],
    }

    remaining_response = client.get(
        f"/api/v1/statistical-tests/saved?model_session_id={model_session_id}"
    )
    assert remaining_response.status_code == 200
    remaining_items = remaining_response.json()
    assert all(item["id"] != saved_items[0]["id"] for item in remaining_items)
