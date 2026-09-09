import json
from pathlib import Path

import dill
import joblib
import pytest
from datasets import ClassLabel, Value
from fastapi.testclient import TestClient

from DashAI.back.core.enums.status import PredictionStatus
from DashAI.back.dataloaders.classes.csv_dataloader import CSVDataLoader
from DashAI.back.dataloaders.classes.json_dataloader import JSONDataLoader
from DashAI.back.dependencies.database.models import Dataset, ModelSession, Run
from DashAI.back.dependencies.registry import ComponentRegistry
from DashAI.back.job.base_job import JobError
from DashAI.back.job.dataset_job import DatasetJob
from DashAI.back.job.model_job import ModelJob
from DashAI.back.job.predict_job import PredictJob
from DashAI.back.metrics.base_metric import BaseMetric
from DashAI.back.models.base_model import BaseModel
from DashAI.back.models.scikit_learn.k_neighbors_classifier import (
    KNeighborsClassifier,
)
from DashAI.back.optimizers.optuna_optimizer import OptunaOptimizer
from DashAI.back.splitters.holdout import HoldoutSplitter
from DashAI.back.tasks.base_task import BaseTask
from DashAI.back.tasks.tabular_classification_task import TabularClassificationTask


class DummyTask(BaseTask):
    name: str = "DummyTask"
    metadata: dict = {
        "inputs_types": [ClassLabel, Value],
        "outputs_types": [ClassLabel],
        "inputs_cardinality": "n",
        "outputs_cardinality": 1,
    }

    def prepare_for_task(self, dataset, output_columns):
        return dataset


class DummyModel(BaseModel):
    COMPATIBLE_COMPONENTS = ["DummyTask"]

    def save(self, filename):
        joblib.dump(self, filename)

    def load(self, filename):
        return

    def predict(self, x):
        return {}

    def train(self, x, y):
        return

    def prepare_dataset(self, dataset, is_fit=False):
        return


class DummyMetric(BaseMetric):
    COMPATIBLE_COMPONENTS = ["DummyTask"]

    @staticmethod
    def score(true_labels: list, probs_pred_labels: list):
        return 1


@pytest.fixture(autouse=True, name="test_registry")
def setup_test_registry(client, monkeypatch: pytest.MonkeyPatch):
    """Setup a test registry with test task, dataloader and model components."""
    container = client.app.container

    test_registry = ComponentRegistry(
        initial_components=[
            DummyTask,
            DummyModel,
            DummyMetric,
            CSVDataLoader,
            JSONDataLoader,
            ModelJob,
            OptunaOptimizer,
            TabularClassificationTask,
            # The run these tests predict with, and the splitter that carved
            # its partitions, both have to be resolvable by name.
            KNeighborsClassifier,
            HoldoutSplitter,
        ]
    )

    monkeypatch.setitem(
        container._services,
        "component_registry",
        test_registry,
    )
    return test_registry


@pytest.fixture(scope="module", name="dataset", autouse=True)
def create_dataset(client: TestClient):
    """Create testing dataset using job system for JSON dataset."""
    abs_file_path = Path(__file__).parent / "irisDataset.json"

    container = client.app.container
    session_factory = container["session_factory"]

    with session_factory() as db:
        json_dataset_entry = Dataset(
            name="test_json",
            file_path="",
        )
        db.add(json_dataset_entry)
        db.commit()
        db.refresh(json_dataset_entry)

        kwargs = {
            "dataset_id": json_dataset_entry.id,
            "url": "",
            "params": {
                "dataloader": "JSONDataLoader",
                "name": json_dataset_entry.name,
                "data_key": "data",
                "schema": {
                    "feature_0": {"type": "Float", "dtype": "float64"},
                    "feature_1": {"type": "Float", "dtype": "float64"},
                    "feature_2": {"type": "Float", "dtype": "float64"},
                    "feature_3": {"type": "Float", "dtype": "float64"},
                    "class": {"type": "Categorical", "dtype": "string"},
                },
            },
            "file_path": abs_file_path,
        }
        job = DatasetJob(job_type="DatasetJob", kwargs=kwargs, db=db)
        job.run()

        db.refresh(json_dataset_entry)

        dataset = {
            "id": json_dataset_entry.id,
            "name": json_dataset_entry.name,
            "file_path": json_dataset_entry.file_path,
        }

    yield dataset

    with session_factory() as db:
        dataset_to_delete = db.get(Dataset, dataset["id"])
        if dataset_to_delete:
            db.delete(dataset_to_delete)
            db.commit()


@pytest.fixture(name="dataset_2", autouse=True, scope="module")
def create_dataset_2(client: TestClient):
    """Create testing dataset 2 using CSV file."""
    abs_file_path = Path(__file__).parent / "iris.csv"

    container = client.app.container
    session_factory = container["session_factory"]

    with session_factory() as db:
        csv_dataset_entry = Dataset(
            name="test_csv",
            file_path="",
        )
        db.add(csv_dataset_entry)
        db.commit()
        db.refresh(csv_dataset_entry)

        kwargs = {
            "dataset_id": csv_dataset_entry.id,
            "url": "",
            "params": {
                "dataloader": "CSVDataLoader",
                "separator": ",",
                "name": csv_dataset_entry.name,
                "schema": {
                    "SepalLengthCm": {"type": "Float", "dtype": "float64"},
                    "SepalWidthCm": {"type": "Float", "dtype": "float64"},
                    "PetalLengthCm": {"type": "Float", "dtype": "float64"},
                    "PetalWidthCm": {"type": "Float", "dtype": "float64"},
                    "Species": {"type": "Categorical", "dtype": "string"},
                },
            },
            "file_path": abs_file_path,
        }
        job = DatasetJob(job_type="DatasetJob", kwargs=kwargs, db=db)
        job.run()

        db.refresh(csv_dataset_entry)

        dataset = {
            "id": csv_dataset_entry.id,
            "name": csv_dataset_entry.name,
            "file_path": csv_dataset_entry.file_path,
        }

    yield dataset

    with session_factory() as db:
        dataset_to_delete = db.get(Dataset, dataset["id"])
        if dataset_to_delete:
            db.delete(dataset_to_delete)
            db.commit()


@pytest.fixture(scope="module", name="model_session_id", autouse=True)
def create_model_session(client: TestClient, dataset: Dataset):
    session_factory = client.app.container["session_factory"]

    with session_factory() as db:
        model_session = ModelSession(
            dataset_id=dataset["id"],
            name="Experiment",
            task_name="TabularClassificationTask",
            input_columns=["feature_0", "feature_1", "feature_2", "feature_3"],
            output_columns=["class"],
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


@pytest.fixture(scope="module", name="run_id")
def create_run_id(client: TestClient, model_session_id: int):
    container = client.app.container
    session_factory = container["session_factory"]

    with session_factory() as db:
        run = Run(
            model_session_id=model_session_id,
            optimizer_name="OptunaOptimizer",
            optimizer_parameters={
                "n_trials": 10,
                "sampler": "TPESampler",
                "pruner": "None",
            },
            model_name="KNeighborsClassifier",
            parameters={},
            name="Run",
            goal_metric="Accuracy",
        )
        db.add(run)
        db.commit()
        db.refresh(run)

        yield run.id

        db.delete(run)
        db.commit()
        db.close()


@pytest.fixture(name="trained_run_id", scope="module", autouse=True)
def create_trained_run(client: TestClient, run_id: int):
    form_data = {"job_type": "ModelJob", "kwargs": json.dumps({"run_id": run_id})}

    response = client.post(
        "/api/v1/job/",
        data=form_data,
    )
    assert response.status_code == 201, response.text

    job_id = response.json()["id"]
    job_status = client.get(f"/api/v1/job/status/{job_id}").json()
    assert job_status["status"] == "finished", f"Model job failed: {job_status}"

    return run_id


@pytest.fixture(scope="module", name="prediction_id", autouse=True)
def create_prediction(client: TestClient, trained_run_id: int, dataset: Dataset):
    response = client.post(
        "/api/v1/predict/",
        json={
            "run_id": trained_run_id,
            "dataset_id": dataset["id"],
        },
    )
    assert response.status_code == 200, response.text

    form_data = {
        "job_type": "PredictJob",
        "kwargs": json.dumps({"prediction_id": response.json()["id"]}),
    }

    enqueued_response = client.post(
        "/api/v1/job/",
        data=form_data,
    )

    assert enqueued_response.status_code == 201, enqueued_response.text

    prediction_id = response.json()["id"]
    return prediction_id


def test_get_all_predictions(
    client: TestClient, trained_run_id: int, prediction_id: int
):
    """Test getting all predictions with optional filtering."""
    # Get all predictions
    response = client.get("/api/v1/predict/")
    assert response.status_code == 200, response.text
    predictions = response.json()
    assert isinstance(predictions, list)
    assert len(predictions) > 0

    # Filter by run_id
    response = client.get("/api/v1/predict/", params={"run_id": trained_run_id})
    assert response.status_code == 200, response.text
    predictions = response.json()
    assert isinstance(predictions, list)
    assert all(pred["run_id"] == trained_run_id for pred in predictions)

    # Filter by prediction_id
    response = client.get("/api/v1/predict/", params={"prediction_id": prediction_id})
    assert response.status_code == 200, response.text
    predictions = response.json()
    assert isinstance(predictions, list)
    assert len(predictions) == 1
    assert predictions[0]["id"] == prediction_id


def test_filter_datasets_endpoint(
    client: TestClient, trained_run_id: int, dataset: Dataset, dataset_2: Dataset
):
    """Test filtering datasets that match the run's input columns."""
    response = client.get(
        "/api/v1/predict/filter_datasets",
        params={"run_id": trained_run_id},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    valid_dataset_ids = body["valid_dataset_ids"]
    assert isinstance(valid_dataset_ids, list)
    assert len(valid_dataset_ids) == 1
    assert dataset["id"] in valid_dataset_ids
    assert dataset_2["id"] not in valid_dataset_ids


def test_delete_prediction(client: TestClient, trained_run_id: int):
    """Test deleting a prediction."""
    # Create a new prediction for deletion test
    response = client.post(
        "/api/v1/predict/",
        json={
            "run_id": trained_run_id,
        },
    )
    assert response.status_code == 200, response.text
    prediction_id = response.json()["id"]

    # Delete the prediction
    response = client.delete(f"/api/v1/predict/{prediction_id}")
    assert response.status_code == 200, response.text

    # Verify it's deleted
    response = client.get("/api/v1/predict/", params={"prediction_id": prediction_id})
    assert response.status_code == 200, response.text
    predictions = response.json()
    assert len(predictions) == 0


def test_prediction_not_found(client: TestClient):
    """Test handling for non-existent prediction."""
    non_existent_id = 99999

    response = client.get("/api/v1/predict/", params={"prediction_id": non_existent_id})
    assert response.status_code == 200, response.text
    assert response.json() == []


def test_run_not_found(client: TestClient):
    """Test error handling for non-existent run."""
    non_existent_run_id = 99999

    response = client.get(
        "/api/v1/predict/filter_datasets", params={"run_id": non_existent_run_id}
    )
    assert response.status_code == 404, response.text
    assert response.json()["detail"] == "Run not found"


def test_splits_endpoint_offers_every_partition_of_an_ordinary_run(
    client: TestClient, trained_run_id: int, dataset: Dataset
):
    """A classifier can be asked about any partition, including the whole set."""
    response = client.get(f"/api/v1/predict/splits/{trained_run_id}")
    assert response.status_code == 200, response.text

    body = response.json()
    assert body["training_dataset_id"] == dataset["id"]
    assert [split["name"] for split in body["splits"]] == [
        "train",
        "test",
        "val",
        "all",
    ]
    assert all(split["rows"] > 0 for split in body["splits"])


def test_splits_endpoint_run_not_found(client: TestClient):
    response = client.get("/api/v1/predict/splits/99999")
    assert response.status_code == 404, response.text
    assert response.json()["detail"] == "Run not found"


def test_a_failing_prediction_reports_why(
    client: TestClient,
    trained_run_id: int,
    dataset: Dataset,
    monkeypatch: pytest.MonkeyPatch,
):
    """The model's own complaint has to survive the trip out of the worker.

    Prediction jobs run in a subprocess and their exception is sent back with
    dill. A starlette HTTPException never reaches the caller: it stores nothing
    in ``args``, so unpickling calls it with no status code and the real
    message is replaced by a deserialisation failure.
    """
    response = client.post(
        "/api/v1/predict/",
        json={"run_id": trained_run_id, "dataset_id": dataset["id"]},
    )
    assert response.status_code == 200, response.text
    prediction_id = response.json()["id"]

    def explode(**kwargs):
        raise ValueError("ARIMA forecasts forward only")

    monkeypatch.setattr("DashAI.back.job.predict_job._run_prediction_pipeline", explode)

    job = PredictJob(job_type="PredictJob", kwargs={"prediction_id": prediction_id})
    with pytest.raises(JobError) as raised:
        job.run()

    assert "ARIMA forecasts forward only" in str(raised.value)
    assert "ARIMA forecasts forward only" in str(dill.loads(dill.dumps(raised.value)))

    # The prediction is left marked as failed rather than running forever.
    response = client.get("/api/v1/predict/", params={"prediction_id": prediction_id})
    assert response.json()[0]["status"] == PredictionStatus.ERROR.value
