import json

import joblib
import pytest
from datasets import ClassLabel, Value
from fastapi.testclient import TestClient

from DashAI.back.dependencies.database.models import (
    Dataset,
    GlobalExplainer,
    LocalExplainer,
    ModelSession,
    Run,
)
from DashAI.back.dependencies.registry import ComponentRegistry
from DashAI.back.explainability.global_explainer import BaseGlobalExplainer
from DashAI.back.explainability.local_explainer import BaseLocalExplainer
from DashAI.back.job.explainer_job import ExplainerJob
from DashAI.back.models.base_model import BaseModel
from DashAI.back.splitters.holdout import HoldoutSplitter
from DashAI.back.splitters.k_fold import KFoldSplitter
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


class DummyModel(BaseModel):
    COMPATIBLE_COMPONENTS = ["DummyTask"]

    @classmethod
    def get_schema(cls):
        return {}

    def save(self, filename):
        joblib.dump(self, filename)

    @staticmethod
    def load(filename):
        # Return a new DummyModel instance for testing
        return DummyModel()

    def predict(self, x):
        return {}

    def train(self, x_train, y_train, x_validation=None, y_validation=None):
        return

    def prepare_dataset(self, dataset, is_fit=False):
        return dataset

    def prepare_output(self, dataset, is_fit=False):
        return dataset


class DummyGlobalExplainer(BaseGlobalExplainer):
    COMPATIBLE_COMPONENTS = ["DummyTask"]

    #: Records the last dataset handed to explain, so tests can assert which
    #: rows the job resolved for the explanation.
    last_dataset = None

    def __init__(self, model: BaseModel) -> None:
        self.model = model
        self.explanation = None

    @classmethod
    def get_schema(cls):
        return {}

    def explain(self, dataset):
        DummyGlobalExplainer.last_dataset = dataset
        return

    def plot(self, explanation):
        return


class DummyLocalExplainer(BaseLocalExplainer):
    COMPATIBLE_COMPONENTS = ["DummyTask"]

    def __init__(self, model: BaseModel) -> None:
        self.model = model
        self.explanation = None

    @classmethod
    def get_schema(cls):
        return {}

    def fit(self, dataset):
        return

    def explain_instance(self, instances):
        return

    def plot(self, explanation):
        return


class MangleModel(DummyModel):
    """Model whose preparation renames the input columns.

    Mirrors bag-of-words style text models, whose ``prepare_dataset``
    replaces the raw input column with the vectorized feature columns.
    """

    COMPATIBLE_COMPONENTS = ["DummyTask"]

    @staticmethod
    def load(filename):
        return MangleModel()

    def prepare_dataset(self, dataset, is_fit=False):
        return dataset.rename_columns(
            {column: f"{column}_prepared" for column in dataset.column_names}
        )


RAW_INPUT_COLUMNS = []


class RawInputLocalExplainer(BaseLocalExplainer):
    """Local explainer that records the columns the job hands it."""

    COMPATIBLE_COMPONENTS = ["DummyTask"]

    def __init__(self, model: BaseModel) -> None:
        self.model = model
        self.explanation = None

    @classmethod
    def get_schema(cls):
        return {}

    def fit(self, dataset, **kwargs):
        return self

    def explain_instance(self, instances):
        columns = instances.column_names
        if isinstance(columns, dict):
            columns = [column for split in columns.values() for column in split]
        RAW_INPUT_COLUMNS.extend(columns)
        return {}

    def plot(self, explanation):
        return


@pytest.fixture(autouse=True, name="test_registry")
def setup_test_registry(client, monkeypatch: pytest.MonkeyPatch):
    """Setup a test registry with test task and explainers components."""
    container = client.app.container

    test_registry = ComponentRegistry(
        initial_components=[
            DummyTask,
            DummyModel,
            MangleModel,
            DummyGlobalExplainer,
            DummyLocalExplainer,
            RawInputLocalExplainer,
            ExplainerJob,
            # Explaining a run asks its splitter which partitions exist, so the
            # splitters the runs under test were created with must be resolvable.
            HoldoutSplitter,
            KFoldSplitter,
        ]
    )

    monkeypatch.setitem(
        container._services,
        "component_registry",
        test_registry,
    )
    return test_registry


@pytest.fixture(scope="module", name="model_session_id", autouse=True)
def create_model_session(client: TestClient, dataset_id: int):
    container = client.app.container
    session_factory = container["session_factory"]

    with session_factory() as db:
        model_session = ModelSession(
            dataset_id=dataset_id,
            name="DummyExperiment",
            task_name="DummyTask",
            input_columns=input_columns,
            output_columns=output_columns,
            evaluation_strategy="test_size",
            splits=splits,
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
            model_name="DummyModel",
            parameters={},
            goal_metric="Accuracy",
            name="Run",
            split_indexes="""{
                "train_indexes": [0, 1, 2, 3, 4],
                "test_indexes": [5, 6, 7, 8],
                "val_indexes": [9, 10, 11, 12]
            }""",
        )
        db.add(run)
        db.commit()
        db.refresh(run)

        yield run.id

        db.delete(run)
        db.commit()
        db.close()


# Create dummys explainers
@pytest.fixture(scope="module", name="global_explainer_id")
def create_global_explainer(client: TestClient, run_id: int):
    container = client.app.container
    session_factory = container["session_factory"]

    with session_factory() as db:
        global_explainer = GlobalExplainer(
            name="test_global",
            run_id=run_id,
            explainer_name="DummyGlobalExplainer",
            parameters={},
        )
        db.add(global_explainer)
        db.commit()
        db.refresh(global_explainer)

        yield global_explainer.id

        db.delete(global_explainer)
        db.commit()
        db.close()


@pytest.fixture(scope="module", name="local_explainer_id")
def create_local_explainer(client: TestClient, run_id: int, dataset_id: int):
    container = client.app.container
    session_factory = container["session_factory"]

    with session_factory() as db:
        local_explainer = LocalExplainer(
            name="test_local",
            run_id=run_id,
            explainer_name="DummyLocalExplainer",
            dataset_id=dataset_id,
            scope={"split": "test", "percentage": 20},
            parameters={},
            fit_parameters={},
        )
        db.add(local_explainer)
        db.commit()
        db.refresh(local_explainer)

        yield local_explainer.id

        db.delete(local_explainer)
        db.commit()
        db.close()


def test_enqueue_explainer_jobs(
    client: TestClient, global_explainer_id: int, local_explainer_id: int
):
    form_data_global = {
        "job_type": "ExplainerJob",
        "kwargs": json.dumps(
            {
                "explainer_id": global_explainer_id,
                "explainer_scope": "global",
            }
        ),
    }

    response = client.post(
        "/api/v1/job/",
        data=form_data_global,
    )
    assert response.status_code == 201, response.text
    created_job = response.json()

    assert "id" in created_job, "Response should contain job ID"
    job_id = created_job["id"]

    response = client.get(f"/api/v1/job/status/{job_id}")
    assert response.status_code == 200, response.text
    job_status = response.json()

    assert job_status["status"] == "finished", (
        f"Job should be finished, got {job_status['status']}"
    )

    response = client.get(f"/api/v1/explainer/global/?run_id={global_explainer_id}")
    assert response.status_code == 200, response.text

    form_data_local = {
        "job_type": "ExplainerJob",
        "kwargs": json.dumps(
            {
                "explainer_id": local_explainer_id,
                "explainer_scope": "local",
            }
        ),
    }

    response = client.post(
        "/api/v1/job/",
        data=form_data_local,
    )
    assert response.status_code == 201, response.text
    created_job_2 = response.json()
    assert "id" in created_job_2
    job_id_2 = created_job_2["id"]
    assert job_id_2 != job_id

    response = client.get(f"/api/v1/job/status/{job_id_2}")
    assert response.status_code == 200, response.text
    job_status_2 = response.json()
    assert job_status_2["status"] == "finished", (
        f"Job should be finished, got {job_status_2['status']}"
    )

    response = client.get("/api/v1/job")
    assert response.status_code == 200, response.text
    gotten_jobs = response.json()
    job_ids = [job["id"] for job in gotten_jobs]
    assert job_id in job_ids
    assert job_id_2 in job_ids


def test_execute_jobs(
    client: TestClient,
    global_explainer_id: int,
    local_explainer_id: int,
    run_id: int,
    dataset_id: int,
):
    form_data_global = {
        "job_type": "ExplainerJob",
        "kwargs": json.dumps(
            {
                "explainer_id": global_explainer_id,
                "explainer_scope": "global",
            }
        ),
    }

    response = client.post(
        "/api/v1/job/",
        data=form_data_global,
    )
    assert response.status_code == 201, response.text
    global_job_id = response.json()["id"]

    form_data_local = {
        "job_type": "ExplainerJob",
        "kwargs": json.dumps(
            {
                "explainer_id": local_explainer_id,
                "explainer_scope": "local",
            }
        ),
    }

    response = client.post(
        "/api/v1/job/",
        data=form_data_local,
    )
    assert response.status_code == 201, response.text
    local_job_id = response.json()["id"]

    response = client.get(f"/api/v1/explainer/global/?run_id={run_id}")
    data = response.json()
    for explainer in data:
        assert explainer["status"] in [
            1,
            3,
        ], f"Explainer status should be 1 or 3, got {explainer['status']}"

    response = client.get(f"/api/v1/explainer/local/?run_id={run_id}")
    data = response.json()
    for explainer in data:
        assert explainer["status"] in [
            1,
            3,
        ], f"Explainer status should be 1 or 3, got {explainer['status']}"

    response = client.get(f"/api/v1/explainer/global/?run_id={run_id}")
    data = response.json()
    for explainer in data:
        assert explainer["status"] == 3, (
            f"Explainer status should be 3 (finished), got {explainer['status']}"
        )

    response = client.get(f"/api/v1/explainer/local/?run_id={run_id}")
    data = response.json()
    for explainer in data:
        assert explainer["status"] == 3, (
            f"Explainer status should be 3 (finished), got {explainer['status']}"
        )

    response = client.get(f"/api/v1/job/status/{global_job_id}")
    assert response.json()["status"] == "finished", (
        f"Global job should be finished, got {response.json()['status']}"
    )

    response = client.get(f"/api/v1/job/status/{local_job_id}")
    assert response.json()["status"] == "finished", (
        f"Local job should be finished, got {response.json()['status']}"
    )


def test_local_explainer_receives_unprepared_model_input(
    client: TestClient, model_session_id: int, dataset_id: int
):
    """The job hands over the instances without the model preparation.

    Explainers query ``model.predict``, which prepares its input itself, so
    preparing beforehand would break models that replace the input column
    with derived features (bag-of-words counts, for instance). Explainers
    needing the model feature space ask for it with ``prepare_model_input``.
    """
    container = client.app.container
    session_factory = container["session_factory"]
    RAW_INPUT_COLUMNS.clear()

    with session_factory() as db:
        run = Run(
            model_session_id=model_session_id,
            optimizer_name="OptunaOptimizer",
            optimizer_parameters={
                "n_trials": 1,
                "sampler": "TPESampler",
                "pruner": "None",
            },
            model_name="MangleModel",
            parameters={},
            goal_metric="Accuracy",
            name="RawInputRun",
            split_indexes="""{
                "train_indexes": [0, 1, 2, 3, 4],
                "test_indexes": [5, 6, 7, 8],
                "val_indexes": [9, 10, 11, 12]
            }""",
        )
        db.add(run)
        db.commit()
        db.refresh(run)

        explainer = LocalExplainer(
            name="test_raw_local",
            run_id=run.id,
            explainer_name="RawInputLocalExplainer",
            dataset_id=dataset_id,
            scope={"split": "test", "percentage": 100},
            parameters={},
            fit_parameters={},
        )
        db.add(explainer)
        db.commit()
        db.refresh(explainer)
        explainer_id = explainer.id

    response = client.post(
        "/api/v1/job/",
        data={
            "job_type": "ExplainerJob",
            "kwargs": json.dumps(
                {"explainer_id": explainer_id, "explainer_scope": "local"}
            ),
        },
    )
    assert response.status_code == 201, response.text
    job_id = response.json()["id"]

    job_status = client.get(f"/api/v1/job/status/{job_id}").json()
    assert job_status["status"] == "finished", (
        f"Job should be finished, got {job_status['status']}"
    )

    assert RAW_INPUT_COLUMNS, "The explainer never received any instance"
    assert set(RAW_INPUT_COLUMNS) == set(input_columns), (
        f"Explainer got prepared columns {sorted(set(RAW_INPUT_COLUMNS))}"
    )


def test_job_with_wrong_explainer(client: TestClient):
    form_data_wrong = {
        "job_type": "ExplainerJob",
        "kwargs": json.dumps({"explainer_id": 31415, "explainer_scope": "local"}),
    }

    response = client.post(
        "/api/v1/job/",
        data=form_data_wrong,
    )

    if response.status_code == 500:
        return

    assert response.status_code == 201, response.text
    job_id = response.json()["id"]

    job_status = client.get(f"/api/v1/job/status/{job_id}").json()
    assert job_status["status"] == "error", (
        f"Job with wrong explainer should fail, got status {job_status['status']}"
    )


def _cv_session(client: TestClient, dataset_id: int, name: str) -> int:
    """Create a session that cross-validates, so its runs resolve to K-Fold."""
    session_factory = client.app.container["session_factory"]
    with session_factory() as db:
        model_session = ModelSession(
            dataset_id=dataset_id,
            name=f"CVExperiment_{name}",
            task_name="DummyTask",
            input_columns=input_columns,
            output_columns=output_columns,
            evaluation_strategy="CrossValidationEvaluationStrategy",
            splits=json.dumps(
                {
                    "splitter_name": "KFoldSplitter",
                    "splitType": "cv",
                    "n_splits": 2,
                    "shuffle": True,
                    "random_state": 42,
                    "test_size": 0.3,
                }
            ),
        )
        db.add(model_session)
        db.commit()
        db.refresh(model_session)
        return model_session.id


def _cv_run(client: TestClient, dataset_id: int, reserved: list, name: str) -> int:
    """Create a finished cross-validation run with the given reserved rows."""
    session_factory = client.app.container["session_factory"]
    with session_factory() as db:
        run = Run(
            model_session_id=_cv_session(client, dataset_id, name),
            optimizer_name="OptunaOptimizer",
            optimizer_parameters={
                "n_trials": 10,
                "sampler": "TPESampler",
                "pruner": "None",
            },
            model_name="DummyModel",
            parameters={},
            goal_metric="Accuracy",
            name=name,
            split_indexes=json.dumps(
                {
                    "fold_0": {
                        "train_indexes": [0, 1, 2, 3],
                        "test_indexes": [4, 5, 6],
                    },
                    "fold_1": {
                        "train_indexes": [4, 5, 6],
                        "test_indexes": [0, 1, 2, 3],
                    },
                    "full_dataset": {
                        "train_indexes": [0, 1, 2, 3, 4, 5, 6],
                        "test_indexes": reserved,
                    },
                }
            ),
        )
        db.add(run)
        db.commit()
        db.refresh(run)
        return run.id


def _global_explainer_for(client: TestClient, run_id: int, name: str) -> int:
    session_factory = client.app.container["session_factory"]
    with session_factory() as db:
        explainer = GlobalExplainer(
            name=name,
            run_id=run_id,
            explainer_name="DummyGlobalExplainer",
            parameters={},
        )
        db.add(explainer)
        db.commit()
        db.refresh(explainer)
        return explainer.id


def _run_explainer_job(client: TestClient, explainer_id: int) -> str:
    response = client.post(
        "/api/v1/job/",
        data={
            "job_type": "ExplainerJob",
            "kwargs": json.dumps(
                {"explainer_id": explainer_id, "explainer_scope": "global"}
            ),
        },
    )
    assert response.status_code == 201, response.text
    job_id = response.json()["id"]

    response = client.get(f"/api/v1/job/status/{job_id}")
    assert response.status_code == 200, response.text
    return response.json()["status"]


def test_cross_validation_run_is_explained_on_its_reserved_rows(
    client: TestClient, dataset_id: int
):
    """The rows kept out of cross-validation are what the explainer receives."""
    run_id = _cv_run(client, dataset_id, [7, 8, 9], "CVWithReservedRows")
    explainer_id = _global_explainer_for(client, run_id, "cv_with_reserved_rows")

    assert _run_explainer_job(client, explainer_id) == "finished"

    # The explainer must receive the reserved rows as its test split, and the
    # rows the folds used as its train split.
    x, _ = DummyGlobalExplainer.last_dataset
    assert len(x["test"]) == 3
    assert len(x["train"]) == 7
    assert len(x["validation"]) == 0

    session_factory = client.app.container["session_factory"]
    with session_factory() as db:
        explainer = db.get(GlobalExplainer, explainer_id)
        assert explainer.explanation_path is not None


def test_cross_validation_run_without_reserved_rows_is_refused(
    client: TestClient, dataset_id: int
):
    """A run that cross-validated every row has nothing an explainer may use."""
    run_id = _cv_run(client, dataset_id, [], "CVWithoutReservedRows")
    explainer_id = _global_explainer_for(client, run_id, "cv_without_reserved_rows")

    assert _run_explainer_job(client, explainer_id) == "error"


def test_explainable_splits_of_a_holdout_run(client: TestClient, run_id: int):
    """A holdout run exposes its three partitions plus the whole dataset."""
    response = client.get(f"/api/v1/explainer/explainable-splits/{run_id}")

    assert response.status_code == 200, response.text
    assert response.json()["splits"] == [
        {"name": "train", "rows": 5},
        {"name": "test", "rows": 4},
        {"name": "val", "rows": 4},
        {"name": "all", "rows": 13},
    ]


def test_explainable_splits_of_a_cross_validation_run(
    client: TestClient, dataset_id: int
):
    """A cross-validation run offers its reserved rows as the test partition."""
    run_id = _cv_run(client, dataset_id, [7, 8, 9], "CVForSplitsEndpoint")

    response = client.get(f"/api/v1/explainer/explainable-splits/{run_id}")

    assert response.status_code == 200, response.text
    assert response.json()["splits"] == [
        {"name": "train", "rows": 7},
        {"name": "test", "rows": 3},
        {"name": "all", "rows": 10},
    ]


def test_explainable_splits_of_a_run_without_reserved_rows(
    client: TestClient, dataset_id: int
):
    """A run that cross-validated every row offers no partition to explain."""
    run_id = _cv_run(client, dataset_id, [], "CVNoHoldoutForSplitsEndpoint")

    response = client.get(f"/api/v1/explainer/explainable-splits/{run_id}")

    assert response.status_code == 200, response.text
    assert response.json()["splits"] == []


def test_explainable_splits_of_a_missing_run(client: TestClient):
    response = client.get("/api/v1/explainer/explainable-splits/99999")

    assert response.status_code == 404, response.text
