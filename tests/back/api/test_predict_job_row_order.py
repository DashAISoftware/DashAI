"""Predicting on a partition reads the rows the task prepared, as training did.

``Run.split_indexes`` are positions in the dataset the task prepared, because
that is what the prepare units partition (``SplitterScopeMixin._prepare``),
and a task may reorder the rows: forecasting sorts them by date. A prediction
on one partition of the run has to select those positions from the prepared
dataset. Selecting them from the loaded one predicts other rows, and nothing
raises: the count is right and the model takes any row.

The run here is trained by ``ModelJob`` on a session whose task reverses the
rows (``row_order_tasks.ReversingTask``), with and without session
preprocessing, which changes the columns the task is prepared with: the raw
refs, as ``PreprocessingJob`` and the prepare units use, instead of the
session's input columns.

Lives under ``tests/back/api`` to reuse the ``client`` and ``dataset_1``
fixtures from this package's ``conftest.py``.
"""

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from DashAI.back.core.enums.status import PredictionStatus
from DashAI.back.dataloaders.classes.dashai_dataset import load_dataset
from DashAI.back.dependencies.database.models import ModelSession, Prediction, Run
from DashAI.back.job.model_job import ModelJob
from DashAI.back.job.predict_job import PredictJob
from tests.back.api.row_order_tasks import ReversingTask

INPUT_COLUMNS = [
    "SepalLengthCm",
    "SepalWidthCm",
    "PetalLengthCm",
    "PetalWidthCm",
]
OUTPUT_COLUMN = "Species"

# In row order and unshuffled, so every partition is a block of positions and
# the reversal moves each block onto rows of another species.
SPLITS = {
    "splitter_name": "HoldoutSplitter",
    "splitType": "random",
    "train": 0.5,
    "test": 0.2,
    "validation": 0.3,
    "shuffle": False,
    "stratify": False,
    "seed": 42,
}
BINARIZER = {
    "converter": "Binarizer",
    "params": {"threshold": 3.0},
    "scope": [{"kind": "raw", "name": "SepalLengthCm"}],
}


@pytest.fixture(name="reversing_task", scope="module")
def register_reversing_task(client: TestClient):
    registry = client.app.container["component_registry"]
    registry.register_component(ReversingTask)
    yield ReversingTask
    registry.unregister_component(ReversingTask)


def _create_session(client, dataset, preprocessing: bool) -> ModelSession:
    body = {
        "dataset_id": dataset.id,
        "task_name": ReversingTask.__name__,
        "name": f"predict-row-order-{'preprocessing' if preprocessing else 'raw'}",
        "input_columns": [] if preprocessing else INPUT_COLUMNS,
        "output_columns": [OUTPUT_COLUMN],
        "train_metrics": [],
        "validation_metrics": [],
        "test_metrics": [],
        "evaluation_strategy": "HoldoutEvaluationStrategy",
        "splits": json.dumps(SPLITS),
        "preprocessing": [BINARIZER] if preprocessing else [],
    }
    if preprocessing:
        body["input_column_refs"] = [{"kind": "group", "step": 0}]

    response = client.post("/api/v1/model-session/", json=body)
    assert response.status_code == 201, response.text
    assert response.json()["preprocessing_status"] in (None, "ready"), response.text

    session_factory = client.app.container["session_factory"]
    with session_factory() as db:
        row = db.get(ModelSession, response.json()["id"])
        db.expunge(row)
        return row


def _train_a_run(client, model_session: ModelSession) -> int:
    session_factory = client.app.container["session_factory"]
    with session_factory() as db:
        run = Run(
            model_session_id=model_session.id,
            model_name="KNeighborsClassifier",
            parameters={},
            optimizer_name="OptunaOptimizer",
            optimizer_parameters={
                "n_trials": 1,
                "sampler": "TPESampler",
                "pruner": "None",
            },
            name=f"{model_session.name}-run",
            goal_metric="Accuracy",
        )
        db.add(run)
        db.commit()
        db.refresh(run)
        run_id = run.id

    ModelJob(run_id=run_id).run()

    with session_factory() as db:
        run = db.get(Run, run_id)
        assert run.run_path, "the run did not produce a saved model"
    return run_id


@pytest.fixture(
    name="trained", scope="module", params=[False, True], ids=["raw", "preprocessing"]
)
def train_on_a_reversing_task(request, client, dataset_1, reversing_task):
    """A run trained by ``ModelJob`` on rows the task handed back reversed."""
    preprocessing = request.param
    model_session = _create_session(client, dataset_1, preprocessing)
    run_id = _train_a_run(client, model_session)

    session_factory = client.app.container["session_factory"]
    with session_factory() as db:
        split_indexes = json.loads(db.get(Run, run_id).split_indexes)

    loaded = load_dataset(str(Path(dataset_1.file_path) / "dataset"))
    # The columns training prepared with: the raw refs when the session
    # preprocesses (none here, the one input is the converter's), the
    # session's inputs otherwise.
    prepared = reversing_task().prepare_for_task(
        loaded, [] if preprocessing else INPUT_COLUMNS, [OUTPUT_COLUMN]
    )
    return {
        "run_id": run_id,
        "split_indexes": split_indexes,
        "loaded": loaded,
        "prepared": prepared,
    }


def _predict(client, run_id, dataset_id, split):
    response = client.post(
        "/api/v1/predict/",
        json={"run_id": run_id, "dataset_id": dataset_id, "split": split},
    )
    assert response.status_code == 200, response.text
    prediction_id = response.json()["id"]

    PredictJob(prediction_id=prediction_id).run()

    session_factory = client.app.container["session_factory"]
    with session_factory() as db:
        prediction = db.get(Prediction, prediction_id)
        assert prediction.status == PredictionStatus.FINISHED
        results_path = prediction.results_path
    return load_dataset(str(Path(results_path) / "dataset"))


@pytest.mark.parametrize(
    ("split", "indexes_key"),
    [("test", "test_indexes"), ("val", "val_indexes")],
)
def test_a_prediction_on_a_partition_reads_the_rows_the_task_prepared(
    client, dataset_1, trained, split, indexes_key
):
    indexes = trained["split_indexes"][indexes_key]
    expected = trained["prepared"].select(indexes).select_columns(INPUT_COLUMNS)
    from_the_loaded_order = (
        trained["loaded"].select(indexes).select_columns(INPUT_COLUMNS)
    )
    # The file is sorted by species, so the two orders hold different rows;
    # without that the assertion below could not tell them apart.
    assert expected.to_dict() != from_the_loaded_order.to_dict()

    saved = _predict(client, trained["run_id"], dataset_1.id, split)

    assert saved.column_names == INPUT_COLUMNS + [OUTPUT_COLUMN]
    assert saved.select_columns(INPUT_COLUMNS).to_dict() == expected.to_dict()
