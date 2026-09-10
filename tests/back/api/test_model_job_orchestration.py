"""End to end regression net for the ModelJob orchestration.

``test_jobs.py`` accepts either ``finished`` or ``error`` as a job outcome, so
it cannot catch a job that silently stops doing part of its work. These tests
pin the observable contract of a successful run: status transitions, the
columns written on ``Run``, the ``Metric`` rows and the saved model artifact.
"""

import json
import os

import joblib
import pytest
from datasets import ClassLabel, Value
from fastapi.testclient import TestClient

from DashAI.back.core.enums.metrics import LevelEnum, SplitEnum
from DashAI.back.core.enums.status import RunStatus
from DashAI.back.core.schema_fields import BaseSchema, int_field, schema_field
from DashAI.back.dataloaders.classes.csv_dataloader import CSVDataLoader
from DashAI.back.dependencies.database.models import (
    Dataset,
    Metric,
    ModelSession,
    Run,
)
from DashAI.back.dependencies.registry import ComponentRegistry
from DashAI.back.evaluation.holdout import HoldoutEvaluationStrategy
from DashAI.back.job.base_job import JobError
from DashAI.back.job.model_job import ModelJob
from DashAI.back.metrics.base_metric import BaseMetric
from DashAI.back.models.base_model import BaseModel
from DashAI.back.optimizers.optuna_optimizer import OptunaOptimizer
from DashAI.back.splitters.holdout import HoldoutSplitter
from DashAI.back.tasks.base_task import BaseTask


class OrchestrationTask(BaseTask):
    name: str = "OrchestrationTask"
    metadata: dict = {
        "inputs_types": [ClassLabel, Value],
        "outputs_types": [ClassLabel],
        "inputs_cardinality": "n",
        "outputs_cardinality": 1,
    }

    def prepare_for_task(self, dataset, input_columns=None, output_columns=None):
        return dataset

    def num_labels(self, dataset, output_column):
        return 3


class OrchestrationModel(BaseModel):
    """Model that records the data it was trained with."""

    COMPATIBLE_COMPONENTS = ["OrchestrationTask"]

    def __init__(self, **kwargs):
        self.trained_with = None

    def save(self, filename):
        joblib.dump({"trained_with": self.trained_with}, filename)

    def load(self, filename):
        return joblib.load(filename)

    def predict(self, x):
        return [0] * x.shape[0]

    def train(self, x_train, y_train, x_validation=None, y_validation=None):
        self.trained_with = {
            "train": x_train.shape[0],
            "validation": None if x_validation is None else x_validation.shape[0],
        }
        return self

    def prepare_dataset(self, dataset, is_fit=False):
        return dataset


class TunableModelSchema(BaseSchema):
    n_estimators: schema_field(
        int_field(gt=0),
        placeholder=2,
        description="Number of estimators.",
    )  # type: ignore


class TunableModel(BaseModel):
    """Model with an optimizable parameter, to exercise the search branch."""

    COMPATIBLE_COMPONENTS = ["OrchestrationTask"]
    SCHEMA = TunableModelSchema

    def __init__(self, n_estimators=2, **kwargs):
        self.n_estimators = n_estimators

    def save(self, filename):
        joblib.dump({"n_estimators": self.n_estimators}, filename)

    def load(self, filename):
        return joblib.load(filename)

    def predict(self, x):
        return [0] * x.shape[0]

    def train(self, x_train, y_train, x_validation=None, y_validation=None):
        return self

    def prepare_dataset(self, dataset, is_fit=False):
        return dataset


class OrchestrationMetric(BaseMetric):
    COMPATIBLE_COMPONENTS = ["OrchestrationTask"]
    MAXIMIZE = True

    @staticmethod
    def score(true_labels, probs_pred_labels):
        return 0.5


class TunableMetric(BaseMetric):
    """Metric whose score depends on the hyperparameter being searched."""

    COMPATIBLE_COMPONENTS = ["OrchestrationTask"]
    MAXIMIZE = True

    @staticmethod
    def score(true_labels, probs_pred_labels):
        return 0.25


@pytest.fixture(scope="module", name="orchestration_registry", autouse=True)
def setup_orchestration_registry(client):
    container = client.app.container
    sentinel = object()
    services = container._services
    old = services.get("component_registry", sentinel)

    services["component_registry"] = ComponentRegistry(
        initial_components=[
            OrchestrationTask,
            OrchestrationModel,
            TunableModel,
            OrchestrationMetric,
            TunableMetric,
            CSVDataLoader,
            ModelJob,
            OptunaOptimizer,
            HoldoutSplitter,
            HoldoutEvaluationStrategy,
        ]
    )
    yield services["component_registry"]
    if old is sentinel:
        del services["component_registry"]
    else:
        services["component_registry"] = old


@pytest.fixture(scope="module", name="model_session_id")
def create_model_session(
    client: TestClient, dataset_1: Dataset, orchestration_registry
):
    session_factory = client.app.container["session_factory"]

    with session_factory() as db:
        model_session = ModelSession(
            dataset_id=dataset_1.id,
            name="OrchestrationSession",
            task_name="OrchestrationTask",
            input_columns=["SepalLengthCm", "SepalWidthCm"],
            output_columns=["Species"],
            train_metrics=["OrchestrationMetric"],
            validation_metrics=["OrchestrationMetric"],
            test_metrics=["OrchestrationMetric"],
            evaluation_strategy="HoldoutEvaluationStrategy",
            splits=json.dumps(
                {
                    "splitter_name": "HoldoutSplitter",
                    "train": 0.5,
                    "test": 0.2,
                    "validation": 0.3,
                    "is_random": True,
                    "has_changed": True,
                    "seed": 42,
                    "shuffle": True,
                    "stratify": False,
                    "splitType": "random",
                }
            ),
        )
        db.add(model_session)
        db.commit()
        db.refresh(model_session)
        yield model_session.id


def _create_run(client: TestClient, model_session_id: int, model_name: str) -> int:
    session_factory = client.app.container["session_factory"]
    with session_factory() as db:
        run = Run(
            model_session_id=model_session_id,
            model_name=model_name,
            parameters={},
            optimizer_name="",
            optimizer_parameters={},
            goal_metric="",
            name="OrchestrationRun",
        )
        db.add(run)
        db.commit()
        db.refresh(run)
        return run.id


@pytest.fixture(name="finished_run")
def run_a_successful_job(client: TestClient, model_session_id: int) -> Run:
    run_id = _create_run(client, model_session_id, "OrchestrationModel")
    ModelJob(run_id=run_id).run()

    session_factory = client.app.container["session_factory"]
    with session_factory() as db:
        return db.get(Run, run_id)


def test_successful_run_reaches_finished(finished_run: Run):
    assert finished_run.status == RunStatus.FINISHED


def test_successful_run_stamps_its_timestamps(finished_run: Run):
    assert finished_run.start_time is not None
    assert finished_run.end_time is not None
    assert finished_run.end_time >= finished_run.start_time


def test_successful_run_persists_the_split_indexes(finished_run: Run):
    split_indexes = json.loads(finished_run.split_indexes)

    assert set(split_indexes) == {"train_indexes", "test_indexes", "val_indexes"}
    assert len(split_indexes["train_indexes"]) > 0
    assert len(split_indexes["val_indexes"]) > 0
    assert len(split_indexes["test_indexes"]) > 0


def test_successful_run_saves_the_model_artifact(finished_run: Run):
    assert finished_run.run_path is not None
    assert finished_run.run_path.endswith(str(finished_run.id))
    assert os.path.exists(finished_run.run_path)


def test_the_model_was_trained_with_the_train_and_validation_splits(
    finished_run: Run,
):
    saved = joblib.load(finished_run.run_path)

    assert saved["trained_with"]["train"] > 0
    assert saved["trained_with"]["validation"] > 0


def test_successful_run_writes_a_last_metric_for_every_split(
    client: TestClient, finished_run: Run
):
    session_factory = client.app.container["session_factory"]
    with session_factory() as db:
        metrics = db.query(Metric).filter_by(run_id=finished_run.id).all()

    by_split = {metric.split: metric for metric in metrics}

    assert set(by_split) == {SplitEnum.TRAIN, SplitEnum.VALIDATION, SplitEnum.TEST}
    for metric in metrics:
        assert metric.level == LevelEnum.LAST
        assert metric.name == "OrchestrationMetric"
        assert metric.value == 0.5


@pytest.fixture(scope="module", name="tuned_run")
def run_a_hyperparameter_search(client: TestClient, model_session_id: int) -> Run:
    """Run the hyperparameter search branch end to end.

    This branch had no coverage at all: every other test creates runs with an
    empty ``optimizer_name`` and no optimizable parameters, so the whole
    optimize/plot path was never executed by the suite.
    """
    session_factory = client.app.container["session_factory"]
    with session_factory() as db:
        run = Run(
            model_session_id=model_session_id,
            model_name="TunableModel",
            parameters={
                "n_estimators": {
                    "optimize": True,
                    "lower_bound": 1,
                    "upper_bound": 5,
                    "fixed_value": 2,
                }
            },
            optimizer_name="OptunaOptimizer",
            optimizer_parameters={
                "n_trials": 3,
                "sampler": "TPESampler",
                "pruner": None,
            },
            goal_metric="TunableMetric",
            name="TunedRun",
        )
        db.add(run)
        db.commit()
        db.refresh(run)
        run_id = run.id

    ModelJob(run_id=run_id).run()

    with session_factory() as db:
        return db.get(Run, run_id)


def test_hyperparameter_search_reaches_finished(tuned_run: Run):
    assert tuned_run.status == RunStatus.FINISHED


def test_hyperparameter_search_persists_the_best_parameters(tuned_run: Run):
    best = tuned_run.parameters["n_estimators"]["fixed_value"]

    assert 1 <= best <= 5


def test_hyperparameter_search_saves_two_plots_for_a_single_parameter(
    tuned_run: Run,
):
    assert tuned_run.plot_history_path is not None
    assert tuned_run.plot_slice_path is not None
    assert os.path.exists(tuned_run.plot_history_path)
    assert os.path.exists(tuned_run.plot_slice_path)
    # create_plots only produces the contour and importance plots when more
    # than one hyperparameter is being searched.
    assert tuned_run.plot_contour_path is None
    assert tuned_run.plot_importance_path is None


def test_the_tuned_model_still_logs_its_metrics(client: TestClient, tuned_run: Run):
    """The optimizer must return the same model instance it received.

    ``ModelFactory`` hangs the run id, the splits and the metric classes off
    the model. If an optimizer returned a fresh object instead,
    ``calculate_metrics`` would silently return and the run would finish with
    no metrics rather than fail.
    """
    session_factory = client.app.container["session_factory"]
    with session_factory() as db:
        metrics = db.query(Metric).filter_by(run_id=tuned_run.id).all()

    last_splits = {m.split for m in metrics if m.level == LevelEnum.LAST}
    assert last_splits == {SplitEnum.TRAIN, SplitEnum.VALIDATION, SplitEnum.TEST}

    # The optimizer logs a metric per trial while searching.
    trial_metrics = [m for m in metrics if m.level == LevelEnum.TRIAL]
    assert len(trial_metrics) > 0


def test_a_missing_run_is_reported_instead_of_crashing(client: TestClient):
    with pytest.raises(JobError, match="Run 987654 does not exist in DB."):
        ModelJob(run_id=987654).run()


def test_an_unknown_model_leaves_the_run_in_error(
    client: TestClient, model_session_id: int
):
    run_id = _create_run(client, model_session_id, "ThereIsNoSuchModel")

    with pytest.raises(JobError, match="Unable to find Model with name"):
        ModelJob(run_id=run_id).run()

    session_factory = client.app.container["session_factory"]
    with session_factory() as db:
        assert db.get(Run, run_id).status == RunStatus.ERROR
