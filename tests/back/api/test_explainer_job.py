"""End-to-end regression net for ``ExplainerJob``.

Written before the job is decomposed into atomic units, and asserted against the
monolithic implementation, so that the refactor has something to be measured
against. The assertions are deliberately explicit — exact status values, exact
columns written on the row, exact error message fragments, and which message is
the one the user actually sees versus which survives only as ``__cause__`` —
instead of the looser ``status in [1, 3]`` style used by
``test_explainer_jobs.py``, which cannot tell a unit that silently stopped doing
part of its work from one that did it.

Tests named ``test_currently_*`` pin behaviour that is known to be wrong. They
exist so the refactor can be proven behaviour-preserving first; the fix lands
afterwards as its own change, which flips the assertion and renames the test.

Lives under ``tests/back/api`` to reuse the ``client`` and ``dataset_1``
fixtures from this package's ``conftest.py``.
"""

import json
import shutil
from pathlib import Path

import joblib
import pytest
from datasets import ClassLabel, Value
from fastapi.testclient import TestClient

from DashAI.back.core.enums.status import ExplainerStatus
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
from DashAI.back.job.base_job import JobError
from DashAI.back.job.explainer_job import ExplainerJob
from DashAI.back.models.base_model import BaseModel
from DashAI.back.tasks.base_task import BaseTask

INPUT_COLUMNS = ["SepalLengthCm", "SepalWidthCm", "PetalLengthCm", "PetalWidthCm"]
OUTPUT_COLUMNS = ["Species"]

SPLIT_INDEXES = json.dumps(
    {
        "train_indexes": [0, 1, 2, 3, 4],
        "test_indexes": [5, 6, 7, 8],
        "val_indexes": [9, 10, 11, 12],
    }
)

SPLITS = json.dumps(
    {
        # The session names the splitter that produced its partitions, which is
        # how every consumer of Run.split_indexes tells a holdout payload from
        # a fold one.
        "splitter_name": "HoldoutSplitter",
        "splitType": "random",
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
        return DummyModel()

    def predict(self, x):
        return {}

    def train(self, x_train, y_train, x_validation=None, y_validation=None):
        return

    def prepare_dataset(self, dataset, is_fit=False):
        return dataset

    def prepare_output(self, dataset, is_fit=False):
        return dataset


class UninstantiableModel(DummyModel):
    def __init__(self, *args, **kwargs):
        raise RuntimeError("this model refuses to be built")


class UnloadableModel(DummyModel):
    @staticmethod
    def load(filename):
        raise OSError("the artifact is not there")


class DummyGlobalExplainer(BaseGlobalExplainer):
    COMPATIBLE_COMPONENTS = ["DummyTask"]

    def __init__(self, model: BaseModel) -> None:
        self.model = model
        self.explanation = None

    @classmethod
    def get_schema(cls):
        return {}

    def explain(self, dataset):
        return {"importance": [1, 2, 3]}

    def plot(self, explanation):
        return "a plot"


class ExplodingGlobalExplainer(DummyGlobalExplainer):
    def explain(self, dataset):
        raise RuntimeError("the explanation itself blew up")


class UninstantiableGlobalExplainer(DummyGlobalExplainer):
    def __init__(self, model: BaseModel) -> None:
        raise RuntimeError("this explainer refuses to be built")


class DummyLocalExplainer(BaseLocalExplainer):
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
        return {"local": True}

    def plot(self, explanation):
        return "a plot"


@pytest.fixture(autouse=True, name="test_registry")
def setup_test_registry(client, monkeypatch: pytest.MonkeyPatch):
    container = client.app.container

    test_registry = ComponentRegistry(
        initial_components=[
            DummyTask,
            DummyModel,
            UninstantiableModel,
            UnloadableModel,
            DummyGlobalExplainer,
            ExplodingGlobalExplainer,
            UninstantiableGlobalExplainer,
            DummyLocalExplainer,
            ExplainerJob,
        ]
    )

    monkeypatch.setitem(container._services, "component_registry", test_registry)
    return test_registry


@pytest.fixture(scope="module", name="model_session_id")
def create_model_session(client: TestClient, dataset_1: Dataset):
    session_factory = client.app.container["session_factory"]

    with session_factory() as db:
        model_session = ModelSession(
            dataset_id=dataset_1.id,
            name="ExplainerJobSession",
            task_name="DummyTask",
            input_columns=INPUT_COLUMNS,
            output_columns=OUTPUT_COLUMNS,
            evaluation_strategy="HoldoutEvaluationStrategy",
            splits=SPLITS,
        )
        db.add(model_session)
        db.commit()
        db.refresh(model_session)
        return model_session.id


@pytest.fixture(name="run_id")
def create_run(client: TestClient, model_session_id: int):
    """Function scoped: the error-branch tests corrupt this row on purpose."""
    session_factory = client.app.container["session_factory"]

    with session_factory() as db:
        run = Run(
            model_session_id=model_session_id,
            optimizer_name="OptunaOptimizer",
            optimizer_parameters={},
            model_name="DummyModel",
            parameters={},
            goal_metric="Accuracy",
            name="ExplainerJobRun",
            run_path="a/saved/model",
            split_indexes=SPLIT_INDEXES,
        )
        db.add(run)
        db.commit()
        db.refresh(run)
        return run.id


def _create_global_explainer(client, run_id, explainer_name="DummyGlobalExplainer"):
    session_factory = client.app.container["session_factory"]
    with session_factory() as db:
        explainer = GlobalExplainer(
            run_id=run_id,
            explainer_name=explainer_name,
            parameters={},
        )
        db.add(explainer)
        db.commit()
        db.refresh(explainer)
        return explainer.id


def _create_local_explainer(client, run_id, dataset_id, scope=None):
    session_factory = client.app.container["session_factory"]
    with session_factory() as db:
        explainer = LocalExplainer(
            run_id=run_id,
            explainer_name="DummyLocalExplainer",
            dataset_id=dataset_id,
            scope=scope if scope is not None else {"split": "test", "percentage": 100},
            parameters={},
            fit_parameters={},
        )
        db.add(explainer)
        db.commit()
        db.refresh(explainer)
        return explainer.id


def _stored(client, model, explainer_id):
    session_factory = client.app.container["session_factory"]
    with session_factory() as db:
        row = db.get(model, explainer_id)
        stored = {
            "status": row.status,
            "explanation_path": row.explanation_path,
            "plot_overrides": row.plot_overrides,
            "huey_id": row.huey_id,
        }
        if model is GlobalExplainer:
            stored["plot_path"] = row.plot_path
        else:
            stored["plots_path"] = row.plots_path
            stored["input_dataset_path"] = row.input_dataset_path
        return stored


# --- happy paths --------------------------------------------------------


def test_a_global_explanation_writes_both_pickles_and_finishes(client, run_id):
    explainer_id = _create_global_explainer(client, run_id)

    ExplainerJob(explainer_id=explainer_id, explainer_scope="global").run()

    stored = _stored(client, GlobalExplainer, explainer_id)
    assert stored["status"] == ExplainerStatus.FINISHED
    assert Path(stored["explanation_path"]).name == (
        f"global_explanation_{explainer_id}.pickle"
    )
    assert Path(stored["plot_path"]).name == (
        f"global_explanation_plot_{explainer_id}.pickle"
    )
    assert Path(stored["explanation_path"]).exists()
    assert Path(stored["plot_path"]).exists()
    # Overrides belong to a previous result and must not survive a re-run.
    assert stored["plot_overrides"] is None


def test_a_local_explanation_writes_its_three_paths_and_finishes(
    client, run_id, dataset_1
):
    """The local row carries an extra artifact the global one does not: the
    selected instances, saved so the frontend can read them back."""
    from DashAI.back.dataloaders.classes.dashai_dataset import load_dataset

    explainer_id = _create_local_explainer(client, run_id, dataset_1.id)

    ExplainerJob(explainer_id=explainer_id, explainer_scope="local").run()

    stored = _stored(client, LocalExplainer, explainer_id)
    assert stored["status"] == ExplainerStatus.FINISHED
    assert Path(stored["explanation_path"]).name == (
        f"local_explanation_{explainer_id}.pickle"
    )
    assert Path(stored["plots_path"]).name == (
        f"local_explanation_plots_{explainer_id}.pickle"
    )
    assert Path(stored["explanation_path"]).exists()
    assert Path(stored["plots_path"]).exists()
    assert stored["plot_overrides"] is None

    saved_input = load_dataset(str(Path(stored["input_dataset_path"]) / "dataset"))
    assert saved_input.column_names == INPUT_COLUMNS
    # scope percentage 100 over the four test indexes.
    assert len(saved_input) == 4


def test_a_rows_scope_explains_exactly_the_marked_rows(client, run_id, dataset_1):
    """Row indexes address the whole dataset; the split does not apply."""
    from DashAI.back.dataloaders.classes.dashai_dataset import load_dataset

    explainer_id = _create_local_explainer(
        client, run_id, dataset_1.id, scope={"mode": "rows", "row_indexes": [0, 7, 42]}
    )

    ExplainerJob(explainer_id=explainer_id, explainer_scope="local").run()

    stored = _stored(client, LocalExplainer, explainer_id)
    assert stored["status"] == ExplainerStatus.FINISHED

    saved_input = load_dataset(str(Path(stored["input_dataset_path"]) / "dataset"))
    assert len(saved_input) == 3


# --- scope selection ----------------------------------------------------


def test_an_invalid_scope_is_rejected_before_anything_is_touched(client, run_id):
    explainer_id = _create_global_explainer(client, run_id)

    with pytest.raises(JobError, match="banana is an invalid explainer type"):
        ExplainerJob(explainer_id=explainer_id, explainer_scope="banana").run()

    # Nothing ran, so the row is untouched.
    assert _stored(client, GlobalExplainer, explainer_id)["status"] == (
        ExplainerStatus.NOT_STARTED
    )


def test_a_missing_explainer_row_is_reported_by_id(client):
    """The missing row must be named, not crash the handler meant to mark it.

    The row is looked up before the guarded block, because the outer
    ``except Exception`` calls ``set_status_as_error`` on that very row — so
    without the check a bad id used to surface as an ``AttributeError`` raised
    by the error handler itself.
    """
    with pytest.raises(
        JobError, match="Explainer with id 999999 does not exist in DB."
    ):
        ExplainerJob(explainer_id=999999, explainer_scope="global").run()


def test_the_huey_id_is_recorded_on_the_row(client, run_id):
    """Like the other three jobs, the queue task id is stored on the row.

    Without it the explanation cannot be matched back to its queue entry.
    """
    explainer_id = _create_global_explainer(client, run_id)

    ExplainerJob(
        explainer_id=explainer_id, explainer_scope="global", huey_id="task-abc"
    ).run()

    assert _stored(client, GlobalExplainer, explainer_id)["huey_id"] == "task-abc"


# --- loading errors -----------------------------------------------------


def test_a_missing_run_is_reported_and_the_row_goes_to_error(client):
    explainer_id = _create_global_explainer(client, run_id=999999)

    with pytest.raises(JobError, match="Run 999999 does not exist in DB."):
        ExplainerJob(explainer_id=explainer_id, explainer_scope="global").run()

    # STARTED is set late, after everything is loaded, so a failure here takes
    # the row straight from NOT_STARTED to ERROR.
    assert _stored(client, GlobalExplainer, explainer_id)["status"] == (
        ExplainerStatus.ERROR
    )


def test_a_missing_model_session_is_reported_by_id(client, run_id):
    explainer_id = _create_global_explainer(client, run_id)

    session_factory = client.app.container["session_factory"]
    with session_factory() as db:
        db.get(Run, run_id).model_session_id = 999999
        db.commit()

    with pytest.raises(JobError, match="Model session 999999 does not exist in DB."):
        ExplainerJob(explainer_id=explainer_id, explainer_scope="global").run()

    assert _stored(client, GlobalExplainer, explainer_id)["status"] == (
        ExplainerStatus.ERROR
    )


def test_a_missing_training_dataset_names_the_id_that_was_looked_up(
    client, run_id, model_session_id
):
    """The message names the dataset the lookup actually used.

    It used to interpolate ``self.explainer_db.dataset_id`` while looking up
    ``model_session.dataset_id`` — and that column exists on ``LocalExplainer``
    and *not* on ``GlobalExplainer``, so in the global scope the "does not
    exist" error was never built at all: an ``AttributeError`` was raised while
    formatting it.
    """
    explainer_id = _create_global_explainer(client, run_id)

    session_factory = client.app.container["session_factory"]
    with session_factory() as db:
        db.get(ModelSession, model_session_id).dataset_id = 999999
        db.commit()
    try:
        with pytest.raises(JobError, match="Dataset 999999 does not exist in DB."):
            ExplainerJob(explainer_id=explainer_id, explainer_scope="global").run()

        assert _stored(client, GlobalExplainer, explainer_id)["status"] == (
            ExplainerStatus.ERROR
        )
    finally:
        with session_factory() as db:
            db.get(ModelSession, model_session_id).dataset_id = (
                db.query(Dataset).filter(Dataset.name == "test_csv_1").first().id
            )
            db.commit()


def test_an_unknown_model_name_is_reported_by_name(client, run_id):
    explainer_id = _create_global_explainer(client, run_id)

    session_factory = client.app.container["session_factory"]
    with session_factory() as db:
        db.get(Run, run_id).model_name = "NoSuchModel"
        db.commit()

    with pytest.raises(
        JobError, match="Unable to find Model with name NoSuchModel in registry."
    ):
        ExplainerJob(explainer_id=explainer_id, explainer_scope="global").run()

    assert _stored(client, GlobalExplainer, explainer_id)["status"] == (
        ExplainerStatus.ERROR
    )


def test_a_model_that_cannot_be_instantiated_is_reported(client, run_id):
    """The job builds the model before loading it, unlike ``PredictJob``."""
    explainer_id = _create_global_explainer(client, run_id)

    session_factory = client.app.container["session_factory"]
    with session_factory() as db:
        db.get(Run, run_id).model_name = "UninstantiableModel"
        db.commit()

    with pytest.raises(JobError, match="Unable to instantiate model"):
        ExplainerJob(explainer_id=explainer_id, explainer_scope="global").run()


def test_a_model_that_cannot_be_loaded_names_the_path(client, run_id):
    explainer_id = _create_global_explainer(client, run_id)

    session_factory = client.app.container["session_factory"]
    with session_factory() as db:
        run = db.get(Run, run_id)
        run.model_name = "UnloadableModel"
        run.run_path = "gone/from/disk"
        db.commit()

    with pytest.raises(JobError, match="Can not load model from path gone/from/disk"):
        ExplainerJob(explainer_id=explainer_id, explainer_scope="global").run()


def test_an_unknown_explainer_name_is_reported_with_the_multiline_message(
    client, run_id
):
    """One line, so it stays readable wherever it surfaces.

    It used to be a triple-quoted f-string, which put a newline and the source
    file's indentation literally inside the text the user reads.
    """
    explainer_id = _create_global_explainer(
        client, run_id, explainer_name="NoSuchExplainer"
    )

    with pytest.raises(JobError) as excinfo:
        ExplainerJob(explainer_id=explainer_id, explainer_scope="global").run()

    assert str(excinfo.value) == (
        "Unable to find the global explainer with name NoSuchExplainer in registry."
    )


def test_an_explainer_that_cannot_be_instantiated_names_the_scope(client, run_id):
    explainer_id = _create_global_explainer(
        client, run_id, explainer_name="UninstantiableGlobalExplainer"
    )

    with pytest.raises(JobError, match="Unable to instantiate global explainer."):
        ExplainerJob(explainer_id=explainer_id, explainer_scope="global").run()


def test_a_dataset_that_cannot_be_loaded_names_the_path(
    client, run_id, dataset_1, tmp_path
):
    explainer_id = _create_global_explainer(client, run_id)

    stored_folder = Path(dataset_1.file_path) / "dataset"
    backup = tmp_path / "explainer-dataset-backup"
    shutil.copytree(stored_folder, backup)
    shutil.rmtree(stored_folder)
    try:
        with pytest.raises(JobError, match="Can not load dataset from path"):
            ExplainerJob(explainer_id=explainer_id, explainer_scope="global").run()

        assert _stored(client, GlobalExplainer, explainer_id)["status"] == (
            ExplainerStatus.ERROR
        )
    finally:
        shutil.copytree(backup, stored_folder)


def test_an_unknown_task_name_is_reported_by_name(client, run_id, model_session_id):
    explainer_id = _create_global_explainer(client, run_id)

    session_factory = client.app.container["session_factory"]
    with session_factory() as db:
        db.get(ModelSession, model_session_id).task_name = "NoSuchTask"
        db.commit()
    try:
        with pytest.raises(
            JobError, match="Unable to find Task with name NoSuchTask in registry"
        ):
            ExplainerJob(explainer_id=explainer_id, explainer_scope="global").run()
    finally:
        with session_factory() as db:
            db.get(ModelSession, model_session_id).task_name = "DummyTask"
            db.commit()


def test_incomplete_split_indexes_report_a_preparation_error(client, run_id, dataset_1):
    """All three splits are read off the run; a missing one is a hard failure.

    The reads happen inside the block whose ``except Exception`` builds the
    generic preparation message, so that wrapper is what the user sees.
    """
    explainer_id = _create_global_explainer(client, run_id)

    session_factory = client.app.container["session_factory"]
    with session_factory() as db:
        db.get(Run, run_id).split_indexes = json.dumps({"train_indexes": [0, 1]})
        db.commit()

    with pytest.raises(JobError, match="Can not prepare dataset"):
        ExplainerJob(explainer_id=explainer_id, explainer_scope="global").run()

    assert _stored(client, GlobalExplainer, explainer_id)["status"] == (
        ExplainerStatus.ERROR
    )


# --- generation errors --------------------------------------------------


def test_a_failing_global_explanation_is_reported_and_errors(client, run_id):
    explainer_id = _create_global_explainer(
        client, run_id, explainer_name="ExplodingGlobalExplainer"
    )

    with pytest.raises(JobError, match="Failed to generate the explanation") as excinfo:
        ExplainerJob(explainer_id=explainer_id, explainer_scope="global").run()

    assert "the explanation itself blew up" in str(excinfo.value.__cause__)
    assert _stored(client, GlobalExplainer, explainer_id)["status"] == (
        ExplainerStatus.ERROR
    )


def test_an_invalid_split_is_swallowed_by_the_preparation_wrapper(
    client, run_id, dataset_1
):
    """The specific complaint never reaches the user.

    ``"notasplit is not a valid split"`` is raised inside the block whose
    ``except Exception`` replaces it with the generic wrapper, so it survives
    only as ``__cause__``. Locking this in because it is an easy detail to
    "fix" by accident while refactoring.
    """
    explainer_id = _create_local_explainer(
        client, run_id, dataset_1.id, scope={"split": "notasplit", "percentage": 100}
    )

    with pytest.raises(JobError, match="Can not prepare Dataset with") as excinfo:
        ExplainerJob(explainer_id=explainer_id, explainer_scope="local").run()

    assert "notasplit is not a valid split" in str(excinfo.value.__cause__)
    assert _stored(client, LocalExplainer, explainer_id)["status"] == (
        ExplainerStatus.ERROR
    )


def test_a_rows_scope_with_no_valid_index_is_swallowed_by_the_same_wrapper(
    client, run_id, dataset_1
):
    explainer_id = _create_local_explainer(
        client,
        run_id,
        dataset_1.id,
        scope={"mode": "rows", "row_indexes": [10**9]},
    )

    with pytest.raises(JobError, match="Can not prepare Dataset with") as excinfo:
        ExplainerJob(explainer_id=explainer_id, explainer_scope="local").run()

    assert "No valid row indexes provided for the explanation" in str(
        excinfo.value.__cause__
    )


def test_a_manual_scope_with_no_rows_is_swallowed_by_the_same_wrapper(
    client, run_id, dataset_1
):
    explainer_id = _create_local_explainer(
        client, run_id, dataset_1.id, scope={"mode": "manual"}
    )

    with pytest.raises(JobError, match="Can not prepare Dataset with") as excinfo:
        ExplainerJob(explainer_id=explainer_id, explainer_scope="local").run()

    assert "No manual input data provided for the explanation" in str(
        excinfo.value.__cause__
    )


def test_a_missing_instance_dataset_is_reported_by_id(client, run_id, dataset_1):
    explainer_id = _create_local_explainer(client, run_id, dataset_1.id)

    session_factory = client.app.container["session_factory"]
    with session_factory() as db:
        db.get(LocalExplainer, explainer_id).dataset_id = 999999
        db.commit()

    with pytest.raises(
        JobError, match="Dataset 999999 to be explained does not exist in DB."
    ):
        ExplainerJob(explainer_id=explainer_id, explainer_scope="local").run()

    assert _stored(client, LocalExplainer, explainer_id)["status"] == (
        ExplainerStatus.ERROR
    )


# --- delivery -----------------------------------------------------------


def test_set_status_as_delivered_marks_the_right_row(client, run_id):
    explainer_id = _create_global_explainer(client, run_id)

    ExplainerJob(
        explainer_id=explainer_id, explainer_scope="global"
    ).set_status_as_delivered()

    assert _stored(client, GlobalExplainer, explainer_id)["status"] == (
        ExplainerStatus.DELIVERED
    )


def test_set_status_as_delivered_rejects_an_invalid_scope(client, run_id):
    explainer_id = _create_global_explainer(client, run_id)

    with pytest.raises(JobError, match="banana is an invalid explainer type"):
        ExplainerJob(
            explainer_id=explainer_id, explainer_scope="banana"
        ).set_status_as_delivered()
