import json
import os

import joblib
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

from DashAI.back.core.config import component_registry
from DashAI.back.database.models import Experiment, Run
from DashAI.back.dataloaders.classes.csv_dataloader import CSVDataLoader
from DashAI.back.metrics import BaseMetric
from DashAI.back.models import BaseModel
from DashAI.back.registries import ComponentRegistry
from DashAI.back.tasks import BaseTask


class DummyTask(BaseTask):
    name: str = "DummyTask"

    def prepare_for_task(self, dataset):
        return {
            "train": {"input": [], "output": []},
            "validation": {"input": [], "output": []},
            "test": {"input": [], "output": []},
        }


class DummyModel(BaseModel):
    COMPATIBLE_COMPONENTS = ["DummyTask"]

    @classmethod
    def get_schema(cls):
        return {}

    def save(self, filename):
        joblib.dump(self, filename)

    def load(self, filename):
        return

    def predict(self, data):
        return {}

    def fit(self, data):
        return


class FailDummyModel(BaseModel):
    COMPATIBLE_COMPONENTS = ["DummyTask"]

    @classmethod
    def get_schema(cls):
        return {}

    def save(self, filename):
        return

    def load(self, filename):
        return

    def predict(self, data):
        return {}

    def fit(self, data):
        raise Exception("Always fails")


class DummyMetric(BaseMetric):
    COMPATIBLE_COMPONENTS = ["DummyTask"]

    @staticmethod
    def score(true_labels: list, probs_pred_labels: list):
        return 1


@pytest.fixture(scope="module", autouse=True)
def override_registry():
    original_registry = component_registry._registry
    original_relationships = component_registry._relationship_manager

    test_registry = ComponentRegistry(
        initial_components=[
            DummyTask,
            DummyModel,
            FailDummyModel,
            DummyMetric,
            CSVDataLoader,
        ]
    )

    # replace the default dataloaders with the previously test dataloaders
    component_registry._registry = test_registry._registry
    component_registry._relationship_manager = test_registry._relationship_manager

    yield test_registry

    # cleanup: restore orginal registers
    component_registry._registry = original_registry
    component_registry._relationship_manager = original_relationships


@pytest.fixture(scope="module", name="dataset_id")
def fixture_dataset_id(client: TestClient):
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


@pytest.fixture(scope="module", name="experiment_id")
def fixture_experiment_id(session: sessionmaker, dataset_id: int):
    db = session()

    experiment = Experiment(
        dataset_id=dataset_id,
        name="DummyExperiment",
        task_name="DummyTask",
        input_columns=json.dumps(
            ["SepalLengthCm", "SepalWidthCm", "PetalLengthCm", "PetalWidthCm"]
        ),
        output_columns=json.dumps(["Species"]),
        splits=json.dumps(
            {
                "train_size": 0.5,
                "test_size": 0.2,
                "val_size": 0.3,
                "seed": 42,
                "shuffle": True,
                "stratify": False,
            }
        ),
    )
    db.add(experiment)
    db.commit()
    db.refresh(experiment)

    yield experiment.id

    db.delete(experiment)
    db.commit()
    db.close()


@pytest.fixture(scope="module", name="run_id")
def fixture_run_id(client: TestClient, experiment_id: int):
    response = client.post(
        "/api/v1/run/",
        json={
            "experiment_id": experiment_id,
            "model_name": "DummyModel",
            "name": "DummyRun",
            "parameters": {},
            "description": "This is a test run",
        },
    )
    assert response.status_code == 201, response.text
    run = response.json()

    yield run["id"]

    response = client.delete(f"/api/v1/run/{run['id']}")
    assert response.status_code == 204, response.text


@pytest.fixture(scope="module", name="failed_run_id")
def fixture_failed_run_id(session: sessionmaker, experiment_id: int):
    db = session()

    run = Run(
        experiment_id=experiment_id,
        model_name="FailDummyModel",
        parameters={},
        name="DummyRun2",
    )
    db.add(run)
    db.commit()
    db.refresh(run)

    yield run.id

    db.delete(run)
    db.commit()
    db.close()


def test_enqueue_jobs(client: TestClient, run_id: int):
    response = client.post("/api/v1/job/runner/", json={"run_id": run_id})
    assert response.status_code == 201, response.text
    created_job = response.json()
    assert created_job["type"] == 0
    assert created_job["run_id"] == run_id

    response = client.get(f"/api/v1/job/{created_job['id']}")
    assert response.status_code == 200, response.text
    gotten_job = response.json()
    assert gotten_job["id"] == created_job["id"]
    assert gotten_job["type"] == created_job["type"]
    assert gotten_job["run_id"] == created_job["run_id"]

    response = client.post("/api/v1/job/runner/", json={"run_id": run_id})
    assert response.status_code == 201, response.text
    created_job_2 = response.json()
    assert created_job_2["id"] != created_job["id"]

    response = client.get("/api/v1/job")
    assert response.status_code == 200, response.text
    gotten_jobs = response.json()
    assert gotten_jobs[0]["id"] == created_job["id"]
    assert gotten_jobs[1]["id"] == created_job_2["id"]


def test_get_all_jobs(client: TestClient, run_id: int):
    # Get all the experiments available in the back
    response = client.get("/api/v1/job")
    assert response.status_code == 200, response.text
    data = response.json()
    assert data[0]["run_id"] == run_id
    assert data[1]["run_id"] == run_id


def test_get_wrong_job(client: TestClient):
    # Try to retrieve a non-existent experiment an get an error
    response = client.get("/api/v1/job/31415")
    assert response.status_code == 404, response.text
    assert response.text == '{"detail":"Job not found"}'


def test_cancel_jobs(client: TestClient):
    response = client.get("/api/v1/job")
    assert response.status_code == 200, response.text
    gotten_jobs = response.json()

    response = client.delete(f"/api/v1/job/?job_id={gotten_jobs[0]['id']}")
    assert response.status_code == 204, response.text

    response = client.get("/api/v1/job")
    assert response.status_code == 200, response.text
    jobs = response.json()
    assert len(jobs) == len(gotten_jobs) - 1
    assert jobs[0]["id"] != gotten_jobs[0]["id"]
    assert jobs[0]["id"] == gotten_jobs[1]["id"]

    response = client.delete(f"/api/v1/job/?job_id={gotten_jobs[1]['id']}")
    assert response.status_code == 204, response.text

    response = client.get("/api/v1/job")
    assert response.status_code == 200, response.text
    jobs = response.json()
    assert jobs == []


def test_execute_jobs(client: TestClient, run_id: int, failed_run_id: int):
    response = client.post("/api/v1/job/runner/", json={"run_id": run_id})
    assert response.status_code == 201, response.text

    response = client.post("/api/v1/job/runner/", json={"run_id": failed_run_id})
    assert response.status_code == 201, response.text

    response = client.get("/api/v1/run")
    data = response.json()
    for run in data:
        assert run["status"] == 1
        assert run["delivery_time"] is not None
        assert run["start_time"] is None
        assert run["end_time"] is None

    response = client.post("/api/v1/job/start/?stop_when_queue_empties=True")
    assert response.status_code == 202, response.text

    response = client.get(f"/api/v1/run/{run_id}")
    data = response.json()
    assert data["status"] == 3
    assert isinstance(data["train_metrics"], dict)
    assert "DummyMetric" in data["train_metrics"]
    assert data["train_metrics"]["DummyMetric"] == 1
    assert data["train_metrics"] == data["validation_metrics"]
    assert data["train_metrics"] == data["test_metrics"]
    assert data["run_path"] is not None
    assert os.path.exists(data["run_path"])
    assert data["status"] == 3
    assert data["delivery_time"] is not None
    assert data["start_time"] is not None
    assert data["end_time"] is not None

    response = client.get(f"/api/v1/run/{failed_run_id}")
    data = response.json()
    assert data["status"] == 4
    assert data["delivery_time"] is not None
    assert data["start_time"] is not None
    assert data["end_time"] is None


def test_job_with_wrong_run(client: TestClient):
    response = client.post("/api/v1/job/runner/", json={"run_id": 31415})
    assert response.status_code == 404, response.text
    assert response.text == '{"detail":"Run not found"}'
