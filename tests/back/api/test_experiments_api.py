import json

import pytest
from fastapi.testclient import TestClient

from DashAI.back.database.models import Dataset


@pytest.fixture(scope="module", name="dataset_id")
def create_dummy_dataset(client: TestClient):
    """Create a dummy dataset for the experiments."""
    container = client.app.container
    session = container.db.provided().session

    with session() as db:
        # Create Dummy Dataset
        dummy_dataset = Dataset(
            name="DummyDataset",
            task_name="TabularClassificationTask",
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


@pytest.fixture(scope="module", name="response_1")
def create_experiment_1(client: TestClient, dataset_id: int):
    """Create experiment 1."""
    return client.post(
        "/api/v1/experiment/",
        json={
            "dataset_id": dataset_id,
            "task_name": "TabularClassificationTask",
            "name": "ExperimentA",
        },
    )


@pytest.fixture(scope="module", name="response_2")
def create_experiment_2(client: TestClient, dataset_id: int):
    """Create experiment 2."""
    return client.post(
        "/api/v1/experiment/",
        json={
            "dataset_id": dataset_id,
            "task_name": "TabularClassificationTask",
            "name": "Experiment2",
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

    # test get experiment by id 2.
    response = client.get("/api/v1/experiment/2")
    assert response.status_code == 200
    data = response.json()
    assert data["dataset_id"] == dataset_id
    assert data["task_name"] == "TabularClassificationTask"
    assert data["name"] == "Experiment2"


def test_get_all_experiments(client: TestClient, dataset_id: int):
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
