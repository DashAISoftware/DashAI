"""The visualization job over a real trained model, end to end.

The dummy model tests in ``test_model_visualization_job`` bypass DashAI's
categorical encoders, so this module trains a real scikit-learn model through
the real ``ModelJob`` first. That exercises the seams the dummies cannot: the
context is built in the model's encoded feature space, and the class names come
back out of the fitted output encoder.
"""

import json
import pickle

import pytest
from fastapi.testclient import TestClient

from DashAI.back.core.enums.status import RunStatus
from DashAI.back.dataloaders.classes.csv_dataloader import CSVDataLoader
from DashAI.back.dependencies.database.models import Dataset, ModelSession, Run
from DashAI.back.dependencies.registry import ComponentRegistry
from DashAI.back.evaluation.holdout import HoldoutEvaluationStrategy
from DashAI.back.job.model_job import ModelJob
from DashAI.back.job.model_visualization_job import ModelVisualizationJob
from DashAI.back.metrics.classification.accuracy import Accuracy
from DashAI.back.models.scikit_learn.decision_tree_classifier import (
    DecisionTreeClassifier,
)
from DashAI.back.optimizers.optuna_optimizer import OptunaOptimizer
from DashAI.back.splitters.holdout import HoldoutSplitter
from DashAI.back.tasks.tabular_classification_task import TabularClassificationTask

INPUT_COLUMNS = ["SepalLengthCm", "SepalWidthCm", "PetalLengthCm", "PetalWidthCm"]
OUTPUT_COLUMNS = ["Species"]


@pytest.fixture(scope="module", name="test_registry", autouse=True)
def setup_test_registry(client):
    """Register the real task, model, metric and both jobs."""
    container = client.app.container
    sentinel = object()
    services = container._services
    old = services.get("component_registry", sentinel)

    test_registry = ComponentRegistry(
        initial_components=[
            TabularClassificationTask,
            DecisionTreeClassifier,
            Accuracy,
            CSVDataLoader,
            ModelJob,
            ModelVisualizationJob,
            OptunaOptimizer,
            HoldoutSplitter,
            HoldoutEvaluationStrategy,
        ]
    )
    services["component_registry"] = test_registry
    yield test_registry
    if old is sentinel:
        del services["component_registry"]
    else:
        services["component_registry"] = old


@pytest.fixture(scope="module", name="model_session_id")
def create_model_session(client: TestClient, dataset_1: Dataset, test_registry):
    session_factory = client.app.container["session_factory"]
    with session_factory() as db:
        model_session = ModelSession(
            dataset_id=dataset_1.id,
            name="RealVisualizationSession",
            task_name="TabularClassificationTask",
            evaluation_strategy="HoldoutEvaluationStrategy",
            input_columns=INPUT_COLUMNS,
            output_columns=OUTPUT_COLUMNS,
            train_metrics=[],
            validation_metrics=[],
            test_metrics=[],
            splits=json.dumps(
                {
                    "train": 0.5,
                    "test": 0.2,
                    "validation": 0.3,
                    "is_random": True,
                    "has_changed": True,
                    "seed": 42,
                    "shuffle": True,
                    "stratify": False,
                    "splitType": "random",
                    "splitter_name": "HoldoutSplitter",
                }
            ),
        )
        db.add(model_session)
        db.commit()
        db.refresh(model_session)

        yield model_session.id

        db.delete(model_session)
        db.commit()


@pytest.fixture(scope="module", name="trained_run_id")
def train_a_real_model(client: TestClient, model_session_id: int, test_registry):
    """Create and train a real decision tree run through ModelJob."""
    response = client.post(
        "/api/v1/run/",
        json={
            "model_session_id": model_session_id,
            "model_name": "DecisionTreeClassifier",
            "name": "RealTreeRun",
            "parameters": {
                "criterion": "gini",
                "max_depth": 3,
                "min_samples_split": 2,
                "min_samples_leaf": 1,
                "max_features": None,
                "class_weight": None,
            },
            "optimizer_name": "",
            "optimizer_parameters": {
                "n_trials": 1,
                "sampler": "TPESampler",
                "pruner": "None",
            },
            "goal_metric": "",
            "description": "A real trained tree",
            "plot_history_path": "path/to/history.png",
            "plot_slice_path": "path/to/slice.png",
            "plot_contour_path": "path/to/contour.png",
            "plot_importance_path": "path/to/importance.png",
        },
    )
    assert response.status_code == 201, response.text
    run_id = response.json()["id"]

    ModelJob(run_id=run_id).run()

    session_factory = client.app.container["session_factory"]
    with session_factory() as db:
        assert db.get(Run, run_id).status == RunStatus.FINISHED

    yield run_id

    client.delete(f"/api/v1/run/{run_id}")


def test_real_model_produces_renderable_artifacts(
    client: TestClient, trained_run_id: int
):
    ModelVisualizationJob(run_id=trained_run_id).run()

    session_factory = client.app.container["session_factory"]
    with session_factory() as db:
        run = db.get(Run, trained_run_id)
        assert run.model_artifacts_status == RunStatus.FINISHED
        artifacts_path = run.model_artifacts_path

    with open(artifacts_path, "rb") as file:
        artifacts = pickle.load(file)

    # The tree diagram followed by the feature importances.
    assert [item["type"] for item in artifacts] == ["plotly", "plotly"]
    assert [item["index"] for item in artifacts] == [0, 1]

    tree_figure = json.loads(artifacts[0]["payload"])
    node_hover = tree_figure["data"][-1]["text"]
    assert node_hover, "the tree diagram carries no nodes"
    # Hover text names the encoded feature the node split on, which is only
    # correct if the context was built in the model's own feature space.
    assert any(column in "".join(node_hover) for column in INPUT_COLUMNS), (
        "no split rule names a real feature"
    )
    # The class distribution is labelled with the decoded species names, which
    # requires the output encoder to have been read back off the model.
    assert "Iris-setosa" in "".join(node_hover)

    importances = json.loads(artifacts[1]["payload"])
    assert set(importances["data"][0]["y"]) == set(INPUT_COLUMNS)


def test_retraining_clears_the_generated_artifacts(
    client: TestClient, trained_run_id: int
):
    ModelVisualizationJob(run_id=trained_run_id).run()
    ModelJob(run_id=trained_run_id).run()

    session_factory = client.app.container["session_factory"]
    with session_factory() as db:
        run = db.get(Run, trained_run_id)
        assert run.model_artifacts_path is None
        assert run.model_artifacts_status is None
