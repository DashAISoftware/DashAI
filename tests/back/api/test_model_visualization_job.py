"""End to end tests for the model visualization job."""

import json
import pickle

import joblib
import pytest
from datasets import ClassLabel, Value
from fastapi.testclient import TestClient

from DashAI.back.core.artifacts import TextArtifact
from DashAI.back.core.enums.status import RunStatus
from DashAI.back.dependencies.database.models import Dataset, ModelSession, Run
from DashAI.back.dependencies.registry import ComponentRegistry
from DashAI.back.job.base_job import JobError
from DashAI.back.job.model_visualization_job import ModelVisualizationJob
from DashAI.back.models.base_model import BaseModel
from DashAI.back.tasks.base_task import BaseTask

input_columns = ["SepalLengthCm", "SepalWidthCm", "PetalLengthCm", "PetalWidthCm"]
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
def dataset_id(dataset_1: Dataset) -> int:
    """Get the dataset ID from the dataset_1 fixture."""
    return dataset_1.id


class DummyTask(BaseTask):
    name: str = "DummyTask"

    metadata: dict = {
        "inputs_types": [ClassLabel, Value],
        "outputs_types": [ClassLabel],
        "inputs_cardinality": "n",
        "outputs_cardinality": 1,
    }

    def prepare_for_task(self, dataset, input_columns=None, output_columns=None):
        return dataset


class PlainModel(BaseModel):
    """A model that does not implement the artifact hook."""

    COMPATIBLE_COMPONENTS = ["DummyTask"]

    @classmethod
    def get_schema(cls):
        return {}

    def save(self, filename):
        joblib.dump(self, filename)

    @staticmethod
    def load(filename):
        return PlainModel()

    def predict(self, x):
        return {}

    def train(self, x_train, y_train, x_validation=None, y_validation=None):
        return

    def prepare_dataset(self, dataset, is_fit=False):
        return dataset

    def prepare_output(self, dataset, is_fit=False):
        return dataset


class VisualModel(PlainModel):
    """A model that reports the feature space it was handed."""

    @staticmethod
    def load(filename):
        return VisualModel()

    def get_model_artifacts(self, context):
        return [
            TextArtifact(payload=",".join(context.feature_names), title="Feature space")
        ]


class ExplodingModel(PlainModel):
    """A model whose hook fails."""

    @staticmethod
    def load(filename):
        return ExplodingModel()

    def get_model_artifacts(self, context):
        raise RuntimeError("boom")


@pytest.fixture(autouse=True, name="test_registry")
def setup_test_registry(client, monkeypatch: pytest.MonkeyPatch):
    """Register the dummy task, models and the job under test."""
    container = client.app.container
    test_registry = ComponentRegistry(
        initial_components=[
            DummyTask,
            PlainModel,
            VisualModel,
            ExplodingModel,
            ModelVisualizationJob,
        ]
    )
    monkeypatch.setitem(container._services, "component_registry", test_registry)
    return test_registry


@pytest.fixture(scope="module", name="model_session_id", autouse=True)
def create_model_session(client: TestClient, dataset_id: int):
    session_factory = client.app.container["session_factory"]
    with session_factory() as db:
        model_session = ModelSession(
            dataset_id=dataset_id,
            name="VisualizationSession",
            task_name="DummyTask",
            evaluation_strategy="HoldoutEvaluationStrategy",
            input_columns=input_columns,
            output_columns=output_columns,
            splits=splits,
        )
        db.add(model_session)
        db.commit()
        db.refresh(model_session)

        yield model_session.id

        db.delete(model_session)
        db.commit()


@pytest.fixture(name="make_run")
def make_run(client: TestClient, model_session_id: int, tmp_path):
    """Build a finished run backed by the given model name."""
    session_factory = client.app.container["session_factory"]
    created = []

    def _make(model_name: str) -> int:
        with session_factory() as db:
            run = Run(
                model_session_id=model_session_id,
                optimizer_name="OptunaOptimizer",
                optimizer_parameters={},
                model_name=model_name,
                parameters={},
                goal_metric="Accuracy",
                name=f"Run for {model_name}",
                run_path=str(tmp_path / f"{model_name}.joblib"),
                status=RunStatus.FINISHED,
                split_indexes=json.dumps(
                    {
                        "train_indexes": [0, 1, 2, 3, 4],
                        "test_indexes": [5, 6, 7, 8],
                        "val_indexes": [9, 10, 11, 12],
                    }
                ),
            )
            db.add(run)
            db.commit()
            db.refresh(run)
            created.append(run.id)
            return run.id

    yield _make

    with session_factory() as db:
        for run_id in created:
            run = db.get(Run, run_id)
            if run:
                db.delete(run)
        db.commit()


def _reload(client: TestClient, run_id: int) -> Run:
    with client.app.container["session_factory"]() as db:
        return db.get(Run, run_id)


def test_job_writes_artifacts_and_marks_finished(client: TestClient, make_run):
    run_id = make_run("VisualModel")
    ModelVisualizationJob(run_id=run_id).run()

    run = _reload(client, run_id)
    assert run.model_artifacts_status == RunStatus.FINISHED
    with open(run.model_artifacts_path, "rb") as file:
        artifacts = pickle.load(file)

    assert len(artifacts) == 1
    assert artifacts[0]["type"] == "text"
    assert artifacts[0]["index"] == 0
    # The hook receives the model's own feature space.
    assert artifacts[0]["payload"].split(",") == input_columns


def test_model_without_the_hook_finishes_empty(client: TestClient, make_run):
    run_id = make_run("PlainModel")
    ModelVisualizationJob(run_id=run_id).run()

    run = _reload(client, run_id)
    assert run.model_artifacts_status == RunStatus.FINISHED
    with open(run.model_artifacts_path, "rb") as file:
        assert pickle.load(file) == []


def test_job_marks_error_when_the_hook_raises(client: TestClient, make_run):
    run_id = make_run("ExplodingModel")
    with pytest.raises(JobError, match="Failed to generate the model visualization"):
        ModelVisualizationJob(run_id=run_id).run()

    assert _reload(client, run_id).model_artifacts_status == RunStatus.ERROR


def test_delivered_status_is_set_before_the_queue_runs(client: TestClient, make_run):
    run_id = make_run("VisualModel")
    ModelVisualizationJob(run_id=run_id).set_status_as_delivered()

    assert _reload(client, run_id).model_artifacts_status == RunStatus.DELIVERED


def test_job_name_uses_the_run_name(client: TestClient, make_run):
    run_id = make_run("VisualModel")
    name = ModelVisualizationJob(run_id=run_id).get_job_name()

    assert name == "Visualize: Run for VisualModel"
