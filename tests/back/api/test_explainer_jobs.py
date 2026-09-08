import json

import joblib
import pytest
from datasets import ClassLabel, Value
from fastapi.testclient import TestClient

from DashAI.back.converters.base_converter import BaseConverter
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


def _save_minimal_reference_partition(preprocessed_path, in_cols, out_cols) -> None:
    """Write a minimal `train/x`/`train/y` reference partition under
    `preprocessed_path` (see `SessionPreprocessingJob.run()`'s on-disk
    layout). `get_real_input_output_columns` (used by `ExplainerJob.run()`)
    reads a session's real column names off this partition whenever
    `preprocessed_path` is set — tests that build a fitted-converters file
    by hand instead of running a real `SessionPreprocessingJob` still need
    this much of the on-disk layout to exist, even though only the column
    *names* (not the values) matter for what those tests verify."""
    import os

    import pyarrow as pa

    from DashAI.back.dataloaders.classes.dashai_dataset import (
        DashAIDataset,
        save_dataset,
    )

    x_table = pa.table({col: pa.array([0.0]) for col in in_cols})
    y_table = pa.table({col: pa.array(["a"]) for col in out_cols})
    save_dataset(DashAIDataset(x_table), os.path.join(preprocessed_path, "train", "x"))
    save_dataset(DashAIDataset(y_table), os.path.join(preprocessed_path, "train", "y"))


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

    def __init__(self, model: BaseModel) -> None:
        self.model = model
        self.explanation = None

    @classmethod
    def get_schema(cls):
        return {}

    def explain(self, dataset):
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


RECORDED_TRANSFORM_COLUMNS = []


class RecordingConverter(BaseConverter):
    """Fake fitted session converter: records the columns it's asked to
    transform, and returns them unchanged. Used to verify that
    `ExplainerJob` actually replays session converters (see
    `_reapply_session_converters` in `explainer_job.py`), without needing a
    real `SessionPreprocessingJob` run."""

    COMPATIBLE_COMPONENTS = ["DummyTask"]
    SCHEMA = None

    def get_output_type(self, column_name=None):
        return None

    def fit(self, x, y=None):
        return self

    def transform(self, x, y=None):
        RECORDED_TRANSFORM_COLUMNS.append(sorted(x.column_names))
        return x


class AppendingConverter(BaseConverter):
    """Fake fitted session converter that *appends* a new column instead of
    transforming in place — mirrors LabelEncoder (`le_<col>`) and BagOfWords
    (`bow_<word>`), which leave the original column sitting alongside
    whatever they add. Used to verify `ExplainerJob` validates/selects the
    *raw* schema before replaying converters (not `model_session
    .input_columns`, which names the converter's *output* and doesn't
    exist in the raw dataset yet)."""

    COMPATIBLE_COMPONENTS = ["DummyTask"]
    SCHEMA = None

    def get_output_type(self, column_name=None):
        import pyarrow as pa

        from DashAI.back.types.value_types import Integer

        return Integer(arrow_type=pa.int64())

    def fit(self, x, y=None):
        return self

    def transform(self, x, y=None):
        import pyarrow as pa

        from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset

        RECORDED_TRANSFORM_COLUMNS.append(sorted(x.column_names))
        table = x.arrow_table.append_column(
            "engineered_col", pa.array([0] * len(x), type=pa.int64())
        )
        types = dict(x.types)
        types["engineered_col"] = self.get_output_type()
        return DashAIDataset(table, types=types, splits=x.splits)


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
            evaluation_strategy="holdout",
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


def test_explainer_reapplies_session_converters(
    client: TestClient, dataset_id: int, tmp_path
):
    """When the session has converters, ExplainerJob must replay the fitted
    ones on both the global explanation's inputs (data_x) and the local
    explanation's explained instances (X) — same reasoning as
    predict_job.py's _run_prediction_pipeline. Builds the fitted-converters
    file by hand (a `RecordingConverter`), instead of running a real
    SessionPreprocessingJob, to test the wiring in isolation."""
    container = client.app.container
    session_factory = container["session_factory"]
    RECORDED_TRANSFORM_COLUMNS.clear()

    preprocessed_path = str(tmp_path / "session_dir")
    fitted_converters = [
        {"instance": RecordingConverter(), "columns": ["SepalLengthCm"]}
    ]
    joblib.dump(fitted_converters, f"{preprocessed_path}_converters.pkl")
    _save_minimal_reference_partition(preprocessed_path, input_columns, output_columns)

    with session_factory() as db:
        model_session = ModelSession(
            dataset_id=dataset_id,
            name="ConverterExplainerSession",
            task_name="DummyTask",
            input_columns=input_columns,
            output_columns=output_columns,
            evaluation_strategy="holdout",
            splits=splits,
            converters=[
                {
                    "converter": "RecordingConverter",
                    "params": {},
                    "columns": ["SepalLengthCm"],
                }
            ],
            preprocessed_path=preprocessed_path,
        )
        db.add(model_session)
        db.commit()
        db.refresh(model_session)
        session_id = model_session.id

        run = Run(
            model_session_id=session_id,
            optimizer_name="OptunaOptimizer",
            optimizer_parameters={
                "n_trials": 1,
                "sampler": "TPESampler",
                "pruner": "None",
            },
            model_name="DummyModel",
            parameters={},
            goal_metric="Accuracy",
            name="ConverterExplainerRun",
            split_indexes="""{
                "train_indexes": [0, 1, 2, 3, 4],
                "test_indexes": [5, 6, 7, 8],
                "val_indexes": [9, 10, 11, 12]
            }""",
        )
        db.add(run)
        db.commit()
        db.refresh(run)
        run_id = run.id

        global_explainer = GlobalExplainer(
            name="test_converter_global",
            run_id=run_id,
            explainer_name="DummyGlobalExplainer",
            parameters={},
        )
        db.add(global_explainer)
        db.commit()
        db.refresh(global_explainer)
        global_explainer_id = global_explainer.id

        local_explainer = LocalExplainer(
            name="test_converter_local",
            run_id=run_id,
            explainer_name="DummyLocalExplainer",
            dataset_id=dataset_id,
            scope={"split": "test", "percentage": 100},
            parameters={},
            fit_parameters={},
        )
        db.add(local_explainer)
        db.commit()
        db.refresh(local_explainer)
        local_explainer_id = local_explainer.id

    try:
        response = client.post(
            "/api/v1/job/",
            data={
                "job_type": "ExplainerJob",
                "kwargs": json.dumps(
                    {"explainer_id": global_explainer_id, "explainer_scope": "global"}
                ),
            },
        )
        assert response.status_code == 201, response.text
        job_status = client.get(f"/api/v1/job/status/{response.json()['id']}").json()
        assert job_status["status"] == "finished", job_status

        assert RECORDED_TRANSFORM_COLUMNS, (
            "the converter was never called for the global explanation"
        )
        assert all(cols == ["SepalLengthCm"] for cols in RECORDED_TRANSFORM_COLUMNS)

        RECORDED_TRANSFORM_COLUMNS.clear()

        response = client.post(
            "/api/v1/job/",
            data={
                "job_type": "ExplainerJob",
                "kwargs": json.dumps(
                    {"explainer_id": local_explainer_id, "explainer_scope": "local"}
                ),
            },
        )
        assert response.status_code == 201, response.text
        job_status = client.get(f"/api/v1/job/status/{response.json()['id']}").json()
        assert job_status["status"] == "finished", job_status

        assert RECORDED_TRANSFORM_COLUMNS, (
            "the converter was never called for the local explanation"
        )
        assert all(cols == ["SepalLengthCm"] for cols in RECORDED_TRANSFORM_COLUMNS)
    finally:
        with session_factory() as db:
            db.delete(db.get(LocalExplainer, local_explainer_id))
            db.delete(db.get(GlobalExplainer, global_explainer_id))
            db.delete(db.get(Run, run_id))
            db.delete(db.get(ModelSession, session_id))
            db.commit()


def test_explainer_handles_converter_that_appends_input_columns(
    client: TestClient, dataset_id: int, tmp_path
):
    """Regression test: a converter that *appends* a new column instead of
    transforming in place (e.g. BagOfWords' `bow_<word>`, LabelEncoder's
    `le_<col>`) used to crash both explanation scopes with a `KeyError` —
    `run()` validated/selected `model_session.input_columns` (the
    converter's *output* name, `engineered_col`) directly against the raw
    dataset, before the fitted converter that actually produces it ever
    ran. Uses `RawInputLocalExplainer` to confirm the local explanation
    doesn't just avoid crashing, but is actually handed `engineered_col` —
    not the original scope column the converter read from."""
    container = client.app.container
    session_factory = container["session_factory"]
    RECORDED_TRANSFORM_COLUMNS.clear()
    RAW_INPUT_COLUMNS.clear()

    preprocessed_path = str(tmp_path / "session_dir_appending")
    fitted_converters = [
        {"instance": AppendingConverter(), "columns": ["SepalLengthCm"]}
    ]
    joblib.dump(fitted_converters, f"{preprocessed_path}_converters.pkl")
    # The session's own final input is `["engineered_col"]` below (the
    # converter's output), not the raw `input_columns` module constant.
    _save_minimal_reference_partition(
        preprocessed_path, ["engineered_col"], output_columns
    )

    with session_factory() as db:
        model_session = ModelSession(
            dataset_id=dataset_id,
            name="AppendingConverterExplainerSession",
            task_name="DummyTask",
            # The session's *final* input is the converter-produced column,
            # not the raw one it was derived from — mirrors picking
            # `bow_<word>`/`le_<col>` in the wizard's Columns step.
            input_columns=["engineered_col"],
            output_columns=output_columns,
            evaluation_strategy="holdout",
            splits=splits,
            converters=[
                {
                    "converter": "AppendingConverter",
                    "params": {},
                    "columns": ["SepalLengthCm"],
                }
            ],
            preprocessed_path=preprocessed_path,
        )
        db.add(model_session)
        db.commit()
        db.refresh(model_session)
        session_id = model_session.id

        run = Run(
            model_session_id=session_id,
            optimizer_name="OptunaOptimizer",
            optimizer_parameters={
                "n_trials": 1,
                "sampler": "TPESampler",
                "pruner": "None",
            },
            model_name="DummyModel",
            parameters={},
            goal_metric="Accuracy",
            name="AppendingConverterExplainerRun",
            split_indexes="""{
                "train_indexes": [0, 1, 2, 3, 4],
                "test_indexes": [5, 6, 7, 8],
                "val_indexes": [9, 10, 11, 12]
            }""",
        )
        db.add(run)
        db.commit()
        db.refresh(run)
        run_id = run.id

        global_explainer = GlobalExplainer(
            name="test_appending_global",
            run_id=run_id,
            explainer_name="DummyGlobalExplainer",
            parameters={},
        )
        db.add(global_explainer)
        db.commit()
        db.refresh(global_explainer)
        global_explainer_id = global_explainer.id

        local_explainer = LocalExplainer(
            name="test_appending_local",
            run_id=run_id,
            explainer_name="RawInputLocalExplainer",
            dataset_id=dataset_id,
            scope={"split": "test", "percentage": 100},
            parameters={},
            fit_parameters={},
        )
        db.add(local_explainer)
        db.commit()
        db.refresh(local_explainer)
        local_explainer_id = local_explainer.id

    try:
        response = client.post(
            "/api/v1/job/",
            data={
                "job_type": "ExplainerJob",
                "kwargs": json.dumps(
                    {"explainer_id": global_explainer_id, "explainer_scope": "global"}
                ),
            },
        )
        assert response.status_code == 201, response.text
        job_status = client.get(f"/api/v1/job/status/{response.json()['id']}").json()
        assert job_status["status"] == "finished", job_status

        # The converter was actually invoked, scoped to the *raw* column it
        # reads from — proof the validate/select step ran on the raw
        # schema, not on `engineered_col` (which doesn't exist yet then).
        assert RECORDED_TRANSFORM_COLUMNS, (
            "the converter was never called for the global explanation"
        )
        assert all(cols == ["SepalLengthCm"] for cols in RECORDED_TRANSFORM_COLUMNS)

        RECORDED_TRANSFORM_COLUMNS.clear()

        response = client.post(
            "/api/v1/job/",
            data={
                "job_type": "ExplainerJob",
                "kwargs": json.dumps(
                    {"explainer_id": local_explainer_id, "explainer_scope": "local"}
                ),
            },
        )
        assert response.status_code == 201, response.text
        job_status = client.get(f"/api/v1/job/status/{response.json()['id']}").json()
        assert job_status["status"] == "finished", job_status

        assert RECORDED_TRANSFORM_COLUMNS, (
            "the converter was never called for the local explanation"
        )
        assert all(cols == ["SepalLengthCm"] for cols in RECORDED_TRANSFORM_COLUMNS)

        # The explainer itself was handed exactly the model's real input
        # (the converter's output), not the raw column left behind.
        assert RAW_INPUT_COLUMNS, "the explainer never received any instance"
        assert set(RAW_INPUT_COLUMNS) == {"engineered_col"}
    finally:
        with session_factory() as db:
            db.delete(db.get(LocalExplainer, local_explainer_id))
            db.delete(db.get(GlobalExplainer, global_explainer_id))
            db.delete(db.get(Run, run_id))
            db.delete(db.get(ModelSession, session_id))
            db.commit()


def test_valid_datasets_uses_raw_schema_when_converters_rename_inputs(
    client: TestClient, dataset_id: int
):
    """Regression test: `/local/valid-datasets` used to compare candidate
    datasets against `model_session.input_columns` directly — for a
    session with a converter that adds/renames input columns (BagOfWords'
    `bow_<word>`, PCA's `pca0`/`pca1`), no dataset (not even the session's
    own training dataset) would ever have those names, so the picker
    always came back empty. It must compare against the training
    dataset's own raw schema instead."""
    container = client.app.container
    session_factory = container["session_factory"]

    with session_factory() as db:
        model_session = ModelSession(
            dataset_id=dataset_id,
            name="ValidDatasetsAppendingSession",
            task_name="DummyTask",
            input_columns=["engineered_col"],
            output_columns=output_columns,
            evaluation_strategy="holdout",
            splits=splits,
            converters=[
                {
                    "converter": "AppendingConverter",
                    "params": {},
                    "columns": ["SepalLengthCm"],
                }
            ],
        )
        db.add(model_session)
        db.commit()
        db.refresh(model_session)
        session_id = model_session.id

        run = Run(
            model_session_id=session_id,
            optimizer_name="OptunaOptimizer",
            optimizer_parameters={
                "n_trials": 1,
                "sampler": "TPESampler",
                "pruner": "None",
            },
            model_name="DummyModel",
            parameters={},
            goal_metric="Accuracy",
            name="ValidDatasetsAppendingRun",
            split_indexes="""{
                "train_indexes": [0, 1, 2, 3, 4],
                "test_indexes": [5, 6, 7, 8],
                "val_indexes": [9, 10, 11, 12]
            }""",
        )
        db.add(run)
        db.commit()
        db.refresh(run)
        run_id = run.id

    try:
        response = client.post(
            "/api/v1/explainer/local/valid-datasets",
            json={"run_id": run_id},
        )
        assert response.status_code == 200, response.text
        assert dataset_id in response.json()["valid_dataset_ids"], response.json()
    finally:
        with session_factory() as db:
            db.delete(db.get(Run, run_id))
            db.delete(db.get(ModelSession, session_id))
            db.commit()
