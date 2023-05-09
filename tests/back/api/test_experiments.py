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
        task_name="TabularClassificationTask",
        file_path="dummy.csv",
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
    response = client.post(
        f"/api/v1/experiment/?dataset_id={dataset_id}&"
        f"task_name=TabularClassificationTask&name=ExperimentA",
    )
    assert response.status_code == 201, response.text
    response = client.post(
        f"/api/v1/experiment/?dataset_id={dataset_id}"
        f"&task_name=TabularClassificationTask&name=Experiment2",
    )
    assert response.status_code == 201, response.text

    response = client.get("/api/v1/experiment/1")
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["dataset_id"] == dataset_id
    assert data["task_name"] == "TabularClassificationTask"
    assert data["name"] == "ExperimentA"
    assert data["step"] == 0

    response = client.get("/api/v1/experiment/2")
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["dataset_id"] == dataset_id
    assert data["task_name"] == "TabularClassificationTask"
    assert data["name"] == "Experiment2"
    assert data["step"] == 0


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
    assert data["step"] == 0
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
