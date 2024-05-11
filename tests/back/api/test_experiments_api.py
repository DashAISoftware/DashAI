import json
import os

import pytest
from fastapi.testclient import TestClient

input_columns_1 = ["SepalLengthCm", "SepalWidthCm", "PetalLengthCm", "PetalWidthCm"]
input_columns_2 = ["SepalLengthCm", "PetalWidthCm"]
output_columns = ["Species"]
splits = json.dumps(
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
)


@pytest.fixture(scope="module", name="dataset_id")
def create_dataset(client):
    """Create testing dataset 1."""
    abs_file_path = os.path.join(os.path.dirname(__file__), "iris.csv")

    with open(abs_file_path, "rb") as csv:
        response = client.post(
            "/api/v1/dataset/",
            data={
                "params": """{  "dataloader": "CSVDataLoader",
                                    "dataset_name": "DummyDataset",
                                    "splits_in_folders": false,
                                    "splits": {
                                        "train_size": 0.8,
                                        "test_size": 0.1,
                                        "val_size": 0.1,
                                        "seed": 42,
                                        "shuffle": true
                                    },
                                    "dataloader_params": {
                                        "separator": ","
                                    }
                                }""",
                "url": "",
            },
            files={"file": ("filename", csv, "text/csv")},
        )
    return response.json()["id"]


@pytest.fixture(scope="module", name="response_1")
def create_experiment_1(client: TestClient, dataset_id):
    """Create experiment 1."""
    return client.post(
        "/api/v1/experiment/",
        json={
            "dataset_id": dataset_id,
            "task_name": "TabularClassificationTask",
            "name": "ExperimentA",
            "input_columns": [1, 2, 3, 4],
            "output_columns": [5],
            "splits": splits,
        },
    )


@pytest.fixture(scope="module", name="response_2")
def create_experiment_2(client: TestClient, dataset_id):
    """Create experiment 2."""
    return client.post(
        "/api/v1/experiment/",
        json={
            "dataset_id": dataset_id,
            "task_name": "TabularClassificationTask",
            "name": "ExperimentB",
            "input_columns": [1, 4],
            "output_columns": [5],
            "splits": splits,
        },
    )


def test_create_and_get_experiment(
    client: TestClient, dataset_id: str, response_1, response_2
):
    """Test that an experiment can be created and retrieved."""
    assert response_1.status_code == 201
    assert response_2.status_code == 201

    # test get experiment by id 1.
    response = client.get("/api/v1/experiment/1")
    assert response.status_code == 200
    data = response.json()
    assert data["dataset_id"] == dataset_id
    assert data["task_name"] == "TabularClassificationTask"
    assert data["name"] == "ExperimentA"
    assert data["input_columns"] == input_columns_1
    assert data["output_columns"] == output_columns
    assert data["splits"] == splits

    # test get experiment by id 2.
    response = client.get("/api/v1/experiment/2")
    assert response.status_code == 200
    data = response.json()
    assert data["dataset_id"] == dataset_id
    assert data["task_name"] == "TabularClassificationTask"
    assert data["name"] == "ExperimentB"
    assert data["input_columns"] == input_columns_2
    assert data["output_columns"] == output_columns
    assert data["splits"] == splits


def test_get_all_experiments(client: TestClient, dataset_id):
    """Test that all experiments can be retrieved."""
    response = client.get("/api/v1/experiment")

    assert response.status_code == 200

    data = response.json()
    assert len(data) == 2
    assert data[0]["dataset_id"] == dataset_id
    assert data[1]["dataset_id"] == dataset_id


def test_not_found_experiment(client: TestClient):
    """Test that a 404 is returned when the experiment is not found."""
    response = client.get("/api/v1/experiment/31415")

    assert response.status_code == 404
    assert response.text == '{"detail":"Experiment not found"}'


def test_update_experiment(client: TestClient, dataset_id: int):
    """Test that an experiment can be updated through a patch call."""

    response = client.patch(
        "/api/v1/experiment/2?task_name=UnknownTask&name=Experiment123",
    )
    assert response.status_code == 200

    # get the updated experiment
    response = client.get("/api/v1/experiment/2")
    assert response.status_code == 200

    data = response.json()
    assert data["dataset_id"] == dataset_id
    assert data["task_name"] == "UnknownTask"
    assert data["name"] == "Experiment123"
    assert data["created"] != data["last_modified"]


def test_update_experiment_step(client: TestClient):
    """Test that an experiment step can be updated through a patch call."""
    response = client.patch(
        "/api/v1/experiment/2",
        data={"params": """{"step": "STARTED"}""", "url": ""},
    )
    assert response.status_code == 304


def test_delete_experiment(client: TestClient):
    """Test that an experiment can be deleted."""

    response = client.delete("/api/v1/experiment/1")
    assert response.status_code == 204, response.text

    response = client.delete("/api/v1/experiment/2")
    assert response.status_code == 204, response.text


def test_get_columns_validation_valid(client: TestClient, dataset_id: int):
    response = client.post(
        "/api/v1/experiment/validation",
        json={
            "task_name": "TabularClassificationTask",
            "dataset_id": dataset_id,
            "inputs_columns": [1, 2, 3, 4],
            "outputs_columns": [5],
        },
    )
    assert response.status_code == 200, response.text
    json = response.json()
    assert json["dataset_status"] == "valid"


def test_get_columns_validation_invalid(client: TestClient, dataset_id: int):
    response = client.post(
        "/api/v1/experiment/validation",
        json={
            "task_name": "ImageClassificationTask",
            "dataset_id": dataset_id,
            "inputs_columns": [1, 2, 3, 4],
            "outputs_columns": [5],
        },
    )
    assert response.status_code == 200, response.text
    json = response.json()
    assert json["dataset_status"] == "invalid"


def test_get_columns_validation_wrong_task_name(client: TestClient, dataset_id: int):
    response = client.post(
        "/api/v1/experiment/validation",
        json={
            "task_name": "TabularClassTask",
            "dataset_id": dataset_id,
            "inputs_columns": [1, 2, 3, 4],
            "outputs_columns": [5],
        },
    )
    assert response.status_code == 404, response.text
    assert (
        response.text == '{"detail":"Task TabularClassTask not found in the registry."}'
    )


def test_get_columns_validation_wrong_dataset(client: TestClient):
    response = client.post(
        "/api/v1/experiment/validation",
        json={
            "task_name": "TabularClassificationTask",
            "dataset_id": 127,
            "inputs_columns": [1, 2, 3, 4],
            "outputs_columns": [5],
        },
    )
    assert response.status_code == 404, response.text
    assert response.text == '{"detail":"Dataset not found"}'
