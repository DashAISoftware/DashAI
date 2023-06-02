import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

from DashAI.back.core import config
from DashAI.back.database.models import Dataset, Experiment, Run
from DashAI.back.metrics import BaseMetric
from DashAI.back.models import BaseModel
from DashAI.back.registries import MetricRegistry, ModelRegistry, TaskRegistry
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
    _compatible_tasks = ["DummyTask"]

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
    _compatible_tasks = ["DummyTask"]

    @staticmethod
    def score(true_labels: list, probs_pred_labels: list):
        return 1


@pytest.fixture(scope="function", autouse=True)
def override_load_dataset():
    # TBD
    return


@pytest.fixture(scope="module", autouse=True)
def override_registry():
    original_task_registry = config.task_registry
    original_model_registry = config.model_registry
    original_metric_registry = config.metric_registry

    task_registry = TaskRegistry(initial_components=[DummyTask])
    model_registry = ModelRegistry(
        initial_components=[DummyModel],
        task_registry=task_registry,
    )
    metric_registry = MetricRegistry(
        initial_components=[DummyMetric],
        task_registry=task_registry,
    )

    # replace the default dataloaders with the previously test dataloaders
    config.task_registry._registry = task_registry._registry
    config.model_registry._registry = model_registry._registry
    config.model_registry.task_component_mapping = model_registry.task_component_mapping
    config.metric_registry._registry = metric_registry._registry
    config.metric_registry.task_component_mapping = (
        metric_registry.task_component_mapping
    )

    deleted_mappings = {
        name: reg
        for name, reg in config.name_registry_mapping.items()
        if name not in ["task", "model", "metric"]
    }
    for name in deleted_mappings:
        del config.name_registry_mapping[name]

    yield

    # cleanup: restore orginal registers
    config.task_registry._registry = original_task_registry._registry
    config.model_registry._registry = original_model_registry._registry
    config.model_registry.task_component_mapping = (
        original_model_registry.task_component_mapping
    )
    config.metric_registry._registry = original_metric_registry._registry
    config.metric_registry.task_component_mapping = (
        original_metric_registry.task_component_mapping
    )
    for name, reg in deleted_mappings.items():
        config.name_registry_mapping[name] = reg


@pytest.fixture(scope="module", name="run_id")
def fixture_run_id(session: sessionmaker):
    db = session()

    dataset = Dataset(name="DummyDataset", task_name="DummyTask", file_path="dummy")
    db.add(dataset)
    db.commit()
    db.refresh(dataset)
    experiment = Experiment(
        dataset_id=dataset.id, name="DummyExperiment", task_name="DummyTask"
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
    db.delete(dataset)
    db.commit()


def test_exec_runs(client: TestClient, run_id: int):
    response = client.post(f"/api/v1/runner/?run_id={run_id}")
    assert response.status_code == 202, response.text

    response = client.get(f"/api/v1/run/{run_id}")
    data = response.json()
    assert data["train_metrics"] is not None
    assert data["validation_metrics"] is not None
    assert data["test_metrics"] is not None
    assert data["run_path"] is not None
    assert data["status"] == 2
    assert data["start_time"] != data["end_time"]


def test_exec_wrong_run(client: TestClient):
    response = client.post("/api/v1/runner/?run_id=31415")
    assert response.status_code == 404, response.text
    assert response.text == '{"detail":"Run not found"}'
