import json
import os

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="module", name="dataset_id")
def create_dataset(client):
    """Create testing dataset 1."""
    abs_file_path = os.path.join(os.path.dirname(__file__), "iris.csv")

    with open(abs_file_path, "rb") as csv:
        response = client.post(
            "/api/v1/dataset/",
            data={
                "params": """{  "dataloader": "CSVDataLoader",
                                    "dataset_name": "DummyDataset2",
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


@pytest.fixture(scope="module", name="experiment_id")
def create_experiment(client: TestClient, dataset_id):
    """Create experiment 1."""
    response = client.post(
        "/api/v1/experiment/",
        json={
            "dataset_id": dataset_id,
            "task_name": "TabularClassificationTask",
            "name": "Test Experiment",
            "input_columns": [1, 2, 3, 4],
            "output_columns": [5],
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
    return response.json()["id"]


def test_create_run(client: TestClient, experiment_id: int):
    # create run using the dummy Experiment
    response = client.post(
        "/api/v1/run/",
        json={
            "experiment_id": experiment_id,
            "model_name": "KNeighborsClassifier",
            "name": "Run1",
            "parameters": {"n_neighbors": 5, "weights": "uniform", "algorithm": "auto"},
            "description": "This is a test run",
        },
    )
    assert response.status_code == 201
    response = client.post(
        "/api/v1/run/",
        json={
            "experiment_id": experiment_id,
            "model_name": "KNeighborsClassifier",
            "name": "Run2",
            "parameters": {
                "n_neighbors": 3,
                "weights": "uniform",
                "algorithm": "kd_tree",
            },
            "description": "This is a test run",
        },
    )
    assert response.status_code == 201
    response = client.get("/api/v1/run/1")
    assert response.status_code == 200
    data = response.json()
    assert data["experiment_id"] == experiment_id
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
    assert data["experiment_id"] == experiment_id
    assert data["model_name"] == "KNeighborsClassifier"
    assert data["name"] == "Run2"
    assert data["status"] == 0
    assert data["parameters"] == {
        "n_neighbors": 3,
        "weights": "uniform",
        "algorithm": "kd_tree",
    }


def test_get_run(client: TestClient):
    response = client.get("/api/v1/run/1")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Run1"
    response = client.get("/api/v1/run/2")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Run2"


def test_get_all_runs(client: TestClient, experiment_id: int):
    response = client.get(f"/api/v1/run/?experiment_id={experiment_id}")
    assert response.status_code == 200
    data = response.json()
    assert data[0]["experiment_id"] == experiment_id
    assert data[1]["experiment_id"] == experiment_id


def test_get_wrong_run(client: TestClient):
    # Try to retrieve a non-existent run an get an error
    response = client.get("/api/v1/run/31415")
    assert response.status_code == 404
    assert response.text == '{"detail":"Run not found"}'


def test_get_wrong_runs(client: TestClient):
    # Try to retrieve a list of runs from a non-existent experiment an get an error
    response = client.get("/api/v1/run/?experiment_id=31415")
    assert response.status_code == 404
    assert response.text == '{"detail":"Runs associated with Experiment not found"}'


def test_modify_run(client: TestClient):
    response = client.patch(
        "/api/v1/run/1?run_name=RunA",
        json={
            "n_neighbors": 3,
            "weights": "uniform",
            "algorithm": "kd_tree",
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
    response = client.patch(
        "/api/v1/run/2?model_name=UnknownModel",
    )
    assert response.status_code == 304


def test_delete_run(client: TestClient):
    # Delete all the runs in the db
    response = client.delete("/api/v1/run/1")
    assert response.status_code == 204
    response = client.delete("/api/v1/run/2")
    assert response.status_code == 204
