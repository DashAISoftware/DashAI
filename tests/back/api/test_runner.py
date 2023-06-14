import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

from DashAI.back.core.config import component_registry
from DashAI.back.database.models import Experiment, Run
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
        return

    def load(self, filename):
        return

    def format_data(self, data):
        return data

    def fit(self, x, y):
        return

    def predict(self, x):
        return {}


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
            DummyMetric,
        ]
    )

    # replace the default dataloaders with the previously test dataloaders
    component_registry._registry = test_registry._registry
    component_registry._relationship_manager = test_registry._relationship_manager

    yield test_registry

    # cleanup: restore orginal registers
    component_registry._registry = original_registry
    component_registry._relationship_manager = original_relationships


@pytest.fixture(scope="module", name="run_id")
def fixture_run_id(session: sessionmaker, client: TestClient):
    db = session()

    script_dir = os.path.dirname(__file__)
    test_dataset = "iris.csv"
    abs_file_path = os.path.join(script_dir, test_dataset)
    with open(abs_file_path, "rb") as csv:
        response = client.post(
            "/api/v1/dataset/",
            data={
                "params": """{  "task_name": "DummyTask",
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

    experiment = Experiment(
        dataset_id=dataset["id"], name="DummyExperiment", task_name="DummyTask"
    )
    db.add(experiment)
    db.commit()
    db.refresh(experiment)
    run = Run(
        experiment_id=experiment.id,
        model_name="DummyModel",
        parameters={},
        name="DummyRun",
    )
    db.add(run)
    db.commit()
    db.refresh(run)

    yield run.id

    db.delete(run)
    db.delete(experiment)
    db.commit()
    response = client.delete(f"/api/v1/dataset/{dataset['id']}")
    assert response.status_code == 204, response.text


def test_exec_runs(client: TestClient, run_id: int):
    response = client.post(f"/api/v1/runner/?run_id={run_id}")
    assert response.status_code == 202, response.text

    response = client.get(f"/api/v1/run/{run_id}")
    data = response.json()
    assert isinstance(data["train_metrics"], dict)
    assert isinstance(data["validation_metrics"], dict)
    assert isinstance(data["test_metrics"], dict)
    assert data["run_path"] is not None
    assert data["status"] == 3
    assert data["delivery_time"] is not None
    assert data["start_time"] is not None
    assert data["end_time"] is not None


def test_exec_wrong_run(client: TestClient):
    response = client.post("/api/v1/runner/?run_id=31415")
    assert response.status_code == 404, response.text
    assert response.text == '{"detail":"Run not found"}'
