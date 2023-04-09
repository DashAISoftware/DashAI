import pytest
from DashAI.back.database.models import Dataset
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from DashAI.back.api.deps import get_db
from fastapi import Depends


@pytest.fixture(scope="module", name="dummy_dataset_id")
def fixture_dummy_dataset_id(db: Session = Depends(get_db)):
    # Create Dummy Dataset
    dummy_dataset = Dataset(
        name="DummyDataset",
        task_name="TabularClassificationTask",
        file_path="dummy.csv",
    )
    db.add(dummy_dataset)
    db.commit()
    db.refresh(dummy_dataset)
    print(dummy_dataset.id)
    yield dummy_dataset.id

    # Delete the dataset
    db.delete(dummy_dataset)
    db.commit()


def test_create_experiment(client: TestClient, dummy_dataset_id: int):
    # Create Experiment using the dummy dataset
    response = client.post(
        "/api/v1/experiment/",
        data={
            "params": f"""{{  "dataset_id": {dummy_dataset_id},
                                "task_name": "TabularClassificationTask",
                            }}""",
            "url": "",
        },
    )
    assert response.status_code == 201, response.text

    response = client.post(
        "/api/v1/experiment/",
        data={
            "params": f"""{{  "dataset_id": {dummy_dataset_id},
                                "task_name": "TabularClassificationTask",
                            }}""",
            "url": "",
        },
    )
    assert response.status_code == 201, response.text

    response = client.get("/api/v1/experiment/1")
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["dataset_id"] == dummy_dataset_id
    assert data["task_name"] == "TabularClassificationTask"
    assert data["step"] == "NOT_STARTED"
    assert data["runs"] == []

    response = client.get("/api/v1/experiment/2")
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["dataset_id"] == dummy_dataset_id
    assert data["task_name"] == "TabularClassificationTask"
    assert data["step"] == "NOT_STARTED"
    assert data["runs"] == []


def test_get_all_experiments(client: TestClient, dummy_dataset_id: int):
    # Get all the experiments available in the back
    response = client.get("/api/v1/experiment/2")
    assert response.status_code == 200, response.text
    data = response.json()
    assert data[0]["dataset_id"] == dummy_dataset_id
    assert data[1]["dataset_id"] == dummy_dataset_id


def test_get_wrong_experiment(client: TestClient):
    # Try to retrieve a non-existent experiment an get an error
    response = client.get("/api/v1/experiment/31415")
    assert response.status_code == 404, response.text
    assert response.text == '{"detail":"Dataset not found"}'


def test_modify_experiment(client: TestClient, dummy_dataset_id: int):
    # Modify an existent experiment
    response = client.patch(
        "/api/v1/experiment/2",
        data={"params": """{"task_name": "UnknownTask"}""", "url": ""},
    )
    assert response.status_code == 201, response.text

    # Get the experiment
    response = client.get("/api/v1/experiment/2")
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["dataset_id"] == dummy_dataset_id
    assert data["task_name"] == "UnknownTask"
    assert data["step"] == "NOT_STARTED"
    assert data["runs"] == []
    assert data["created"] != data["last_modified"]


def test_modify_experiment_step(client: TestClient):
    response = client.patch(
        "/api/v1/experiment/2",
        data={"params": """{"step": "STARTED"}""", "url": ""},
    )
    assert response.status_code == 403, response.text
    assert response.text == '{"detail":"Can not modify experiment step"}'


def test_delete_experiment(client: TestClient):
    # Delete the first experiment in the db
    response = client.delete("/api/v1/dataset/1")
    assert response.status_code == 204, response.text
