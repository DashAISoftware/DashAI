import json
import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

from DashAI.back.database.models import Dataset


@pytest.fixture(scope="module", name="dataset_id")
def fixture_dataset_id(session: sessionmaker):
    db = session()
    # Create Dummy Dataset
    dummy_dataset = Dataset(
        name="DummyDataset",
        file_path="dummy.csv",
        feature_names=json.dumps([]),
    )
    db.add(dummy_dataset)
    db.commit()
    db.refresh(dummy_dataset)
    yield dummy_dataset.id

    # Delete the dataset
    db.delete(dummy_dataset)
    db.commit()


def test_create_experiment(client: TestClient, dataset_id: int):
    # Create Experiment using the dummy dataset
    input_columns_A = json.dumps(
        ["SepalLengthCm", "SepalWidthCm", "PetalLengthCm", "PetalWidthCm"]
    )
    input_columns_B = json.dumps(["SepalLengthCm", "PetalWidthCm"])
    output_columns = json.dumps(["Species"])
    splits = json.dumps(
        {
            "train_size": 0.8,
            "test_size": 0.1,
            "val_size": 0.1,
            "seed": 42,
            "shuffle": True,
            "stratify": False,
        }
    )
    response = client.post(
        "/api/v1/experiment/",
        json={
            "dataset_id": dataset_id,
            "task_name": "TabularClassificationTask",
            "name": "ExperimentA",
            "input_columns": input_columns_A,
            "output_columns": output_columns,
            "splits": splits,
        },
    )
    assert response.status_code == 201, response.text
    response = client.post(
        "/api/v1/experiment/",
        json={
            "dataset_id": dataset_id,
            "task_name": "TabularClassificationTask",
            "name": "ExperimentB",
            "input_columns": input_columns_B,
            "output_columns": output_columns,
            "splits": splits,
        },
    )
    assert response.status_code == 201, response.text

    response = client.get("/api/v1/experiment/1")
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["dataset_id"] == dataset_id
    assert data["task_name"] == "TabularClassificationTask"
    assert data["name"] == "ExperimentA"
    assert data["input_columns"] == input_columns_A
    assert data["output_columns"] == output_columns
    assert data["splits"] == splits

    response = client.get("/api/v1/experiment/2")
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["dataset_id"] == dataset_id
    assert data["task_name"] == "TabularClassificationTask"
    assert data["name"] == "ExperimentB"
    assert data["input_columns"] == input_columns_B
    assert data["output_columns"] == output_columns
    assert data["splits"] == splits


def test_get_all_experiments(client: TestClient, dataset_id: int):
    # Get all the experiments available in the back
    response = client.get("/api/v1/experiment")
    assert response.status_code == 200, response.text
    data = response.json()
    assert data[0]["dataset_id"] == dataset_id
    assert data[1]["dataset_id"] == dataset_id


def test_get_wrong_experiment(client: TestClient):
    # Try to retrieve a non-existent experiment an get an error
    response = client.get("/api/v1/experiment/31415")
    assert response.status_code == 404, response.text
    assert response.text == '{"detail":"Experiment not found"}'


def test_modify_experiment(client: TestClient, dataset_id: int):
    # Modify an existent experiment
    response = client.patch(
        "/api/v1/experiment/2?task_name=UnknownTask&name=Experiment123",
    )
    assert response.status_code == 200, response.text

    # Get the experiment
    response = client.get("/api/v1/experiment/2")
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["dataset_id"] == dataset_id
    assert data["task_name"] == "UnknownTask"
    assert data["name"] == "Experiment123"
    assert data["created"] != data["last_modified"]


def test_modify_experiment_step(client: TestClient):
    response = client.patch(
        "/api/v1/experiment/2",
        data={"params": """{"step": "STARTED"}""", "url": ""},
    )
    assert response.status_code == 304, response.text


def test_delete_experiment(client: TestClient):
    # Delete all the experiments in the db
    response = client.delete("/api/v1/experiment/1")
    assert response.status_code == 204, response.text
    response = client.delete("/api/v1/experiment/2")
    assert response.status_code == 204, response.text


@pytest.fixture(scope="module", name="iris_dataset_id")
def fixture_iris_dataset_id(client: TestClient):
    script_dir = os.path.dirname(__file__)
    test_dataset = "iris.csv"
    abs_file_path = os.path.join(script_dir, test_dataset)
    with open(abs_file_path, "rb") as csv:
        response = client.post(
            "/api/v1/dataset/",
            data={
                "params": """{  "task_name": "TabularClassificationTask",
                                    "dataloader": "CSVDataLoader",
                                    "dataset_name": "test_csv2",
                                    "outputs_columns": [],
                                    "splits_in_folders": false,
                                    "splits": {
                                        "train_size": 0.5,
                                        "test_size": 0.2,
                                        "val_size": 0.3,
                                        "seed": 42,
                                        "shuffle": true,
                                        "stratify": false
                                    },
                                    "dataloader_params": {
                                        "separator": ","
                                    }
                                }""",
                "url": "",
            },
            files={"file": ("filename", csv, "text/csv")},
        )
    assert response.status_code == 201, response.text
    dataset = response.json()

    yield dataset["id"]

    response = client.delete(f"/api/v1/dataset/{dataset['id']}")
    assert response.status_code == 204, response.text


def test_get_columns_validation_invalid(client: TestClient, iris_dataset_id: int):
    with pytest.raises(TypeError):
        client.post(
            "/api/v1/experiment/validation",
            json={
                "task_name": "TabularClassificationTask",
                "dataset_id": iris_dataset_id,
                "inputs_columns": [1, 2, 3, 4],
                "outputs_columns": [5],
            },
        )


def test_get_columns_validation_wrong_task_name(
    client: TestClient, iris_dataset_id: int
):
    response = client.post(
        "/api/v1/experiment/validation",
        json={
            "task_name": "TabularClassTask",
            "dataset_id": iris_dataset_id,
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
