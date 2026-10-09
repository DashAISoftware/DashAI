import json

import pytest
from fastapi.testclient import TestClient

from DashAI.back.dependencies.database.models import Dataset

input_columns_1 = ["SepalLengthCm", "SepalWidthCm", "PetalLengthCm", "PetalWidthCm"]
input_columns_2 = ["SepalLengthCm", "PetalWidthCm"]
output_columns = ["Species"]
splits = json.dumps(
    {
        "train": 0.5,
        "test": 0.2,
        "validation": 0.3,
        "seed": 42,
        "shuffle": True,
        "stratify": False,
    }
)


@pytest.fixture(scope="module", name="dataset_id")
def dataset_id(dataset_1: Dataset) -> int:
    """Get the dataset ID from the dataset_1 fixture."""
    return dataset_1.id


@pytest.fixture(scope="module", name="response_1")
def create_model_session_1(client: TestClient, dataset_id: int):
    """Create model session 1."""
    return client.post(
        "/api/v1/model-session/",
        json={
            "dataset_id": dataset_id,
            "task_name": "TabularClassificationTask",
            "name": "ExperimentA",
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
            "splits": splits,
        },
    )


@pytest.fixture(scope="module", name="response_2")
def create_model_session_2(client: TestClient, dataset_id: int):
    """Create model session 2."""
    return client.post(
        "/api/v1/model-session/",
        json={
            "dataset_id": dataset_id,
            "task_name": "TabularClassificationTask",
            "name": "ExperimentB",
            "input_columns": ["SepalLengthCm", "PetalWidthCm"],
            "output_columns": ["Species"],
            "train_metrics": [],
            "validation_metrics": [],
            "test_metrics": [],
            "evaluation_strategy": "holdout",
            "splits": splits,
        },
    )


def test_create_and_get_model_session(
    client: TestClient, dataset_id: str, response_1, response_2
):
    """Test that a model session can be created and retrieved."""
    assert response_1.status_code == 201
    assert response_2.status_code == 201

    # test get model session by id 1.
    response = client.get("/api/v1/model-session/1")
    assert response.status_code == 200
    data = response.json()
    assert data["dataset_id"] == dataset_id
    assert data["task_name"] == "TabularClassificationTask"
    assert data["name"] == "ExperimentA"
    assert data["input_columns"] == input_columns_1
    assert data["output_columns"] == output_columns
    assert data["splits"] == splits
    assert data["evaluation_strategy"] == "holdout"

    # test get model session by id 2.
    response = client.get("/api/v1/model-session/2")
    assert response.status_code == 200
    data = response.json()
    assert data["dataset_id"] == dataset_id
    assert data["task_name"] == "TabularClassificationTask"
    assert data["name"] == "ExperimentB"
    assert data["input_columns"] == input_columns_2
    assert data["output_columns"] == output_columns
    assert data["splits"] == splits
    assert data["evaluation_strategy"] == "holdout"


def test_get_all_model_sessions(client: TestClient, dataset_id: int):
    """Test that all model sessions can be retrieved."""
    response = client.get("/api/v1/model-session")

    assert response.status_code == 200

    data = response.json()
    assert len(data) == 2
    assert data[0]["dataset_id"] == dataset_id
    assert data[1]["dataset_id"] == dataset_id


def test_not_found_model_session(client: TestClient):
    """Test that a 404 is returned when the model session is not found."""
    response = client.get("/api/v1/model-session/31415")

    assert response.status_code == 404
    assert response.text == '{"detail":"Model session not found"}'


def test_update_model_session(client: TestClient, dataset_id: int):
    """Test that a model session can be updated through a patch call."""

    response = client.patch(
        "/api/v1/model-session/2?task_name=UnknownTask&name=ModelSession123",
    )
    assert response.status_code == 200

    # get the updated model session
    response = client.get("/api/v1/model-session/2")
    assert response.status_code == 200

    data = response.json()
    assert data["dataset_id"] == dataset_id
    assert data["task_name"] == "UnknownTask"
    assert data["name"] == "ModelSession123"
    assert data["created"] != data["last_modified"]


def test_update_model_session_step(client: TestClient):
    """Test that a model session step can be updated through a patch call."""
    response = client.patch(
        "/api/v1/model-session/2",
        data={"params": """{"step": "STARTED"}""", "url": ""},
    )
    assert response.status_code == 304


def test_delete_model_session(client: TestClient):
    """Test that a model session can be deleted."""

    response = client.delete("/api/v1/model-session/1")
    assert response.status_code == 204, response.text

    response = client.delete("/api/v1/model-session/2")
    assert response.status_code == 204, response.text


def test_get_columns_validation_valid(client: TestClient, dataset_id: int):
    response = client.post(
        "/api/v1/model-session/validation",
        json={
            "task_name": "TabularClassificationTask",
            "dataset_id": dataset_id,
            "inputs_columns": [
                "SepalLengthCm",
                "SepalWidthCm",
                "PetalLengthCm",
                "PetalWidthCm",
            ],
            "outputs_columns": ["Species"],
        },
    )
    assert response.status_code == 200, response.text
    json = response.json()
    assert json["dataset_status"] == "valid"


def test_get_columns_validation_wrong_task_name(client: TestClient, dataset_id: int):
    response = client.post(
        "/api/v1/model-session/validation",
        json={
            "task_name": "TabularClassTask",
            "dataset_id": dataset_id,
            "inputs_columns": [
                "SepalLengthCm",
                "SepalWidthCm",
                "PetalLengthCm",
                "PetalWidthCm",
            ],
            "outputs_columns": ["Species"],
        },
    )
    assert response.status_code == 404, response.text
    assert (
        response.text == '{"detail":"Task TabularClassTask not found in the registry."}'
    )


def test_get_columns_validation_wrong_dataset(client: TestClient):
    response = client.post(
        "/api/v1/model-session/validation",
        json={
            "task_name": "TabularClassificationTask",
            "dataset_id": 127,
            "inputs_columns": [
                "SepalLengthCm",
                "SepalWidthCm",
                "PetalLengthCm",
                "PetalWidthCm",
            ],
            "outputs_columns": ["Species"],
        },
    )
    assert response.status_code == 404, response.text
    assert response.text == '{"detail":"Dataset not found"}'
