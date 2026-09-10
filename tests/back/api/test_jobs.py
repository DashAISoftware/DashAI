import json
import os

import joblib
import pytest
from datasets import ClassLabel, Value
from fastapi.testclient import TestClient

from DashAI.back.dataloaders.classes.csv_dataloader import CSVDataLoader
from DashAI.back.dependencies.database.models import Dataset, ModelSession, Run
from DashAI.back.dependencies.registry import ComponentRegistry
from DashAI.back.evaluation.holdout import HoldoutEvaluationStrategy
from DashAI.back.job.model_job import ModelJob
from DashAI.back.metrics.base_metric import BaseMetric
from DashAI.back.models.base_model import BaseModel
from DashAI.back.optimizers.optuna_optimizer import OptunaOptimizer
from DashAI.back.splitters.holdout import HoldoutSplitter
from DashAI.back.tasks.base_task import BaseTask


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

    def num_labels(self, dataset, output_column):
        return None


class DummyModel(BaseModel):
    COMPATIBLE_COMPONENTS = ["DummyTask"]

    def save(self, filename):
        joblib.dump(self, filename)

    def load(self, filename):
        return

    def predict(self, x):
        return {}

    def train(self, x_train, y_train, x_validation=None, y_validation=None):
        return

    def prepare_dataset(self, dataset, is_fit=False):
        return


class FailDummyModel(BaseModel):
    COMPATIBLE_COMPONENTS = ["DummyTask"]

    def save(self, filename):
        return

    def load(self, filename):
        return

    def predict(self, x):
        return {}

    def train(self, x_train, y_train, x_validation=None, y_validation=None):
        raise Exception("Always fails")

    def prepare_dataset(self, dataset, is_fit=False):
        return


class DummyMetric(BaseMetric):
    COMPATIBLE_COMPONENTS = ["DummyTask"]

    @staticmethod
    def score(true_labels: list, probs_pred_labels: list):
        return 1


@pytest.fixture(scope="module", name="test_registry", autouse=True)
def setup_test_registry(client):
    """Setup a test registry with test task, dataloader and model components.

    Module-scoped (with a manual swap, since ``monkeypatch`` is function
    scoped) so the test components are registered before the module-scoped
    ``create_run`` / ``create_model_session`` fixtures run.
    """
    container = client.app.container
    sentinel = object()
    services = container._services
    old = services.get("component_registry", sentinel)

    test_registry = ComponentRegistry(
        initial_components=[
            DummyTask,
            DummyModel,
            FailDummyModel,
            DummyMetric,
            CSVDataLoader,
            ModelJob,
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


@pytest.fixture(scope="module", name="dataset_id")
def dataset_id(dataset_1: Dataset) -> int:
    """Get the dataset ID from the dataset_1 fixture."""
    return dataset_1.id


@pytest.fixture(scope="module", name="model_session_id", autouse=True)
def create_model_session(client: TestClient, dataset_id: int, test_registry):
    container = client.app.container
    session = container["session_factory"]

    with session() as db:
        model_session = ModelSession(
            dataset_id=dataset_id,
            name="DummyExperiment",
            task_name="DummyTask",
            input_columns=["SepalLengthCm"],
            output_columns=["Species"],
            train_metrics=[],
            validation_metrics=[],
            test_metrics=[],
            evaluation_strategy="HoldoutEvaluationStrategy",
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
        db.close()


@pytest.fixture(scope="module", name="run_id", autouse=True)
def create_run(client: TestClient, model_session_id: int, test_registry):
    response = client.post(
        "/api/v1/run/",
        json={
            "model_session_id": model_session_id,
            "model_name": "DummyModel",
            "name": "DummyRun",
            "parameters": {},
            "optimizer_name": "",
            "optimizer_parameters": {
                "n_trials": 10,
                "sampler": "TPESampler",
                "pruner": "None",
            },
            "goal_metric": "",
            "description": "This is a test run",
            "plot_history_path": "path/to/history.png",
            "plot_slice_path": "path/to/slice.png",
            "plot_contour_path": "path/to/contour.png",
            "plot_importance_path": "path/to/importance.png",
        },
    )
    assert response.status_code == 201, response.text
    run = response.json()

    yield run["id"]

    response = client.delete(f"/api/v1/run/{run['id']}")
    assert response.status_code == 204, response.text


@pytest.fixture(scope="module", name="failed_run_id", autouse=True)
def create_failed_run(client: TestClient, model_session_id: int, test_registry):
    container = client.app.container
    session_factory = container["session_factory"]

    with session_factory() as db:
        run = Run(
            model_session_id=model_session_id,
            model_name="FailDummyModel",
            parameters={},
            optimizer_name="",
            optimizer_parameters={
                "n_trials": 10,
                "sampler": "TPESampler",
                "pruner": "None",
            },
            goal_metric="",
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
    form_data = {"job_type": "ModelJob", "kwargs": json.dumps({"run_id": run_id})}

    response = client.post("/api/v1/job/", data=form_data)
    assert response.status_code == 201, response.text
    job_id = response.json()["id"]

    response = client.get(f"/api/v1/job/status/{job_id}")
    assert response.status_code == 200, response.text
    job_status = response.json()

    assert job_status["status"] in [
        "finished",
        "error",
    ], f"Job status should be finished or error, got {job_status['status']}"
    if job_status["status"] == "error":
        assert "error" in job_status, "Error jobs should have an error message"

    response = client.post(
        "/api/v1/job/",
        data={"job_type": "ModelJob", "kwargs": json.dumps({"run_id": run_id})},
    )
    assert response.status_code == 201, response.text
    job_id_2 = response.json()["id"]
    assert job_id_2 != job_id, "Job IDs should be different"

    response = client.get(f"/api/v1/job/status/{job_id_2}")
    assert response.status_code == 200, response.text
    job_status_2 = response.json()
    assert job_status_2["status"] in ["finished", "error"]

    response = client.get("/api/v1/job")
    assert response.status_code == 200, response.text
    job_list = response.json()
    job_ids = [job["id"] for job in job_list]
    assert job_id in job_ids, f"Job ID {job_id} not found in job list"
    assert job_id_2 in job_ids, f"Job ID {job_id_2} not found in job list"


def test_execute_jobs(client: TestClient, run_id: int, failed_run_id: int):
    response = client.post(
        "/api/v1/job/",
        data={"job_type": "ModelJob", "kwargs": json.dumps({"run_id": run_id})},
    )
    assert response.status_code == 201, response.text
    job_id = response.json()["id"]

    response = client.post(
        "/api/v1/job/",
        data={"job_type": "ModelJob", "kwargs": json.dumps({"run_id": failed_run_id})},
    )
    assert response.status_code == 201, response.text
    failed_job_id = response.json()["id"]

    response = client.get("/api/v1/run")
    data = response.json()
    for run in data:
        assert run["status"] in [1, 3, 4]
        assert run["delivery_time"] is not None

    response = client.get(f"/api/v1/job/status/{job_id}")
    assert response.status_code == 200, response.text
    assert response.json()["status"] == "finished"

    response = client.get(f"/api/v1/job/status/{failed_job_id}")
    assert response.status_code == 200, response.text
    assert response.json()["status"] == "error"

    response = client.get(f"/api/v1/run/{run_id}")
    data = response.json()
    assert data["status"] == 3
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
    response = client.post(
        "/api/v1/job/",
        data={"job_type": "ModelJob", "kwargs": json.dumps({"run_id": 31415})},
    )
    assert response.status_code == 500, response.text
    assert response.status_code == 500, response.text


def _run_with_splits(
    client: TestClient, model_session_id: int, splits: dict, run_name: str
):
    """Train a run over a session temporarily configured with given splits.

    Parameters
    ----------
    client : TestClient
        The API test client.
    model_session_id : int
        Session whose splits are swapped for the duration of the call.
    splits : dict
        The splits payload to store on the session.
    run_name : str
        Name for the run created over that session.

    Returns
    -------
    tuple
        (job status string, split indexes stored on the run).
    """
    container = client.app.container
    session_factory = container["session_factory"]

    with session_factory() as db:
        model_session = db.get(ModelSession, model_session_id)
        original_splits = model_session.splits
        model_session.splits = json.dumps(splits)
        db.commit()

    response = client.post(
        "/api/v1/run/",
        json={
            "model_session_id": model_session_id,
            "model_name": "DummyModel",
            "name": run_name,
            "parameters": {},
            "optimizer_name": "",
            "optimizer_parameters": {
                "n_trials": 10,
                "sampler": "TPESampler",
                "pruner": "None",
            },
            "goal_metric": "",
            "description": "Run over a specific splits payload",
            "plot_history_path": "path/to/history.png",
            "plot_slice_path": "path/to/slice.png",
            "plot_contour_path": "path/to/contour.png",
            "plot_importance_path": "path/to/importance.png",
        },
    )
    assert response.status_code == 201, response.text
    run_id = response.json()["id"]

    try:
        response = client.post(
            "/api/v1/job/",
            data={"job_type": "ModelJob", "kwargs": json.dumps({"run_id": run_id})},
        )
        assert response.status_code == 201, response.text
        job_id = response.json()["id"]

        response = client.get(f"/api/v1/job/status/{job_id}")
        assert response.status_code == 200, response.text
        status = response.json()["status"]

        with session_factory() as db:
            run = db.get(Run, run_id)
            split_indexes = json.loads(run.split_indexes) if run.split_indexes else None

        return status, split_indexes
    finally:
        with session_factory() as db:
            db.get(ModelSession, model_session_id).splits = original_splits
            db.commit()
        client.delete(f"/api/v1/run/{run_id}")


def test_manual_splits_from_the_splitter_schema_train(
    client: TestClient, model_session_id: int
):
    """The payload the wizard writes for a manual split trains as given."""
    status, split_indexes = _run_with_splits(
        client,
        model_session_id,
        {
            "splitter_name": "HoldoutSplitter",
            "splitType": "manual",
            "splitted_indexes": {
                "train_indexes": [0, 1, 2, 3, 4, 5],
                "test_indexes": [6, 7],
                "val_indexes": [8, 9],
            },
            "stratify": False,
            "shuffle": True,
            "random_state": 42,
        },
        "SchemaManualSplitRun",
    )

    assert status == "finished"
    assert split_indexes == {
        "train_indexes": [0, 1, 2, 3, 4, 5],
        "test_indexes": [6, 7],
        "val_indexes": [8, 9],
    }


def test_random_splits_honor_the_random_state(
    client: TestClient, model_session_id: int
):
    """The seed reaches the splitter, so two seeds give two different splits."""
    base = {
        "splitter_name": "HoldoutSplitter",
        "splitType": "random",
        "train": 0.6,
        "test": 0.2,
        "validation": 0.2,
        "stratify": False,
        "shuffle": True,
    }

    first_status, first = _run_with_splits(
        client, model_session_id, {**base, "random_state": 1}, "SeedOneRun"
    )
    other_status, other = _run_with_splits(
        client, model_session_id, {**base, "random_state": 99}, "SeedNinetyNineRun"
    )

    assert first_status == "finished"
    assert other_status == "finished"
    assert first["train_indexes"] != other["train_indexes"]


def test_legacy_manual_splits_still_train(client: TestClient, model_session_id: int):
    """A session stored before the splits payload followed the splitter schema.

    Manual and predefined holdout splits used to be stored with the partition
    indexes under the ``train`` / ``test`` / ``validation`` keys, which the
    splitter reads as proportions.
    """
    container = client.app.container
    session_factory = container["session_factory"]

    with session_factory() as db:
        model_session = db.get(ModelSession, model_session_id)
        original_splits = model_session.splits
        model_session.splits = json.dumps(
            {
                "splitter_name": "HoldoutSplitter",
                "splitType": "manual",
                "train": [0, 1, 2, 3, 4, 5],
                "test": [6, 7],
                "validation": [8, 9],
            }
        )
        db.commit()

    response = client.post(
        "/api/v1/run/",
        json={
            "model_session_id": model_session_id,
            "model_name": "DummyModel",
            "name": "LegacyManualSplitRun",
            "parameters": {},
            "optimizer_name": "",
            "optimizer_parameters": {
                "n_trials": 10,
                "sampler": "TPESampler",
                "pruner": "None",
            },
            "goal_metric": "",
            "description": "Run over a legacy manual split payload",
            "plot_history_path": "path/to/history.png",
            "plot_slice_path": "path/to/slice.png",
            "plot_contour_path": "path/to/contour.png",
            "plot_importance_path": "path/to/importance.png",
        },
    )
    assert response.status_code == 201, response.text
    run_id = response.json()["id"]

    try:
        response = client.post(
            "/api/v1/job/",
            data={"job_type": "ModelJob", "kwargs": json.dumps({"run_id": run_id})},
        )
        assert response.status_code == 201, response.text
        job_id = response.json()["id"]

        response = client.get(f"/api/v1/job/status/{job_id}")
        assert response.status_code == 200, response.text
        assert response.json()["status"] == "finished"

        with session_factory() as db:
            run = db.get(Run, run_id)
            assert json.loads(run.split_indexes) == {
                "train_indexes": [0, 1, 2, 3, 4, 5],
                "test_indexes": [6, 7],
                "val_indexes": [8, 9],
            }
    finally:
        with session_factory() as db:
            db.get(ModelSession, model_session_id).splits = original_splits
            db.commit()
        client.delete(f"/api/v1/run/{run_id}")


def test_execute_job_with_stale_run_path(client: TestClient, model_session_id: int):
    """A leftover file/dir at run_path (e.g. from a run that reused this id)
    must not prevent training from finishing."""
    container = client.app.container
    session_factory = container["session_factory"]
    config = container["config"]

    with session_factory() as db:
        run = Run(
            model_session_id=model_session_id,
            model_name="DummyModel",
            parameters={},
            optimizer_name="",
            optimizer_parameters={
                "n_trials": 10,
                "sampler": "TPESampler",
                "pruner": "None",
            },
            goal_metric="",
            name="DummyRunStalePath",
        )
        db.add(run)
        db.commit()
        db.refresh(run)
        run_id = run.id

    # Simulate a directory left behind by a previously-deleted run that
    # happened to reuse this same id.
    stale_run_path = os.path.join(config["RUNS_PATH"], str(run_id))
    os.makedirs(stale_run_path, exist_ok=True)
    with open(os.path.join(stale_run_path, "leftover.txt"), "w") as f:
        f.write("stale")

    response = client.post(
        "/api/v1/job/",
        data={"job_type": "ModelJob", "kwargs": json.dumps({"run_id": run_id})},
    )
    assert response.status_code == 201, response.text
    job_id = response.json()["id"]

    response = client.get(f"/api/v1/job/status/{job_id}")
    assert response.status_code == 200, response.text
    assert response.json()["status"] == "finished", response.json()

    response = client.get(f"/api/v1/run/{run_id}")
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["status"] == 3
    assert os.path.isfile(data["run_path"])

    client.delete(f"/api/v1/run/{run_id}")


def test_delete_model_session_cleans_up_run_files(
    client: TestClient, dataset_id: int, test_registry, tmp_path
):
    """Deleting a ModelSession cascades its Runs in the DB, but the
    on-disk run_path/plot files must also be cleaned up, not orphaned."""
    container = client.app.container
    session_factory = container["session_factory"]

    run_dir = tmp_path / "cleanup_run"
    run_dir.mkdir()
    plot_file = tmp_path / "plot.png"
    plot_file.write_text("x")

    with session_factory() as db:
        model_session = ModelSession(
            dataset_id=dataset_id,
            name="CleanupSession",
            task_name="DummyTask",
            input_columns=["SepalLengthCm"],
            output_columns=["Species"],
            train_metrics=[],
            validation_metrics=[],
            test_metrics=[],
            evaluation_strategy="HoldoutEvaluationStrategy",
            splits=json.dumps(
                {
                    "train": 0.5,
                    "test": 0.2,
                    "validation": 0.3,
                    "seed": 42,
                    "shuffle": True,
                    "stratify": False,
                }
            ),
        )
        db.add(model_session)
        db.commit()
        db.refresh(model_session)
        ms_id = model_session.id

        run = Run(
            model_session_id=ms_id,
            model_name="DummyModel",
            parameters={},
            optimizer_name="",
            optimizer_parameters={},
            goal_metric="",
            name="CleanupRun",
            run_path=str(run_dir),
            plot_history_path=str(plot_file),
        )
        db.add(run)
        db.commit()

    response = client.delete(f"/api/v1/model-session/{ms_id}")
    assert response.status_code == 204, response.text
    assert not run_dir.exists()
    assert not plot_file.exists()
