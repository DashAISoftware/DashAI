"""End-to-end regression net for training a clustering session.

Written against ``feat/clustering-units`` before clustering is re-expressed
over the units, and asserted against that implementation, so the integration
has something to be measured against. It only observes what a user or the
database can see -- the rows the API writes, the ``Run`` and ``Metric`` rows the
job leaves, the model on disk and the exact text of every error -- and never
calls a helper of the job, because those helpers are what the integration
replaces.

The sessions and runs are created through the API with the payload the front
sends for a task without a target: no output columns, no metrics, the
``FullDatasetEvaluationStrategy`` its task offers and no splitter, so an empty
splits payload. Rows the API refuses on purpose (an unknown model) are written
straight to the database.
"""

import json
import os
import shutil
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from fastapi.testclient import TestClient
from sklearn.metrics import (
    calinski_harabasz_score,
    davies_bouldin_score,
    silhouette_score,
)
from sklearn.preprocessing import StandardScaler

from DashAI.back.core.enums.metrics import LevelEnum, SplitEnum
from DashAI.back.core.enums.status import PredictionStatus, RunStatus
from DashAI.back.dependencies.database.models import (
    Dataset,
    Metric,
    ModelSession,
    Prediction,
    Run,
)
from DashAI.back.job.base_job import JobError
from DashAI.back.job.dataset_job import DatasetJob
from DashAI.back.job.model_job import ModelJob
from DashAI.back.job.predict_job import PredictJob
from DashAI.back.metrics.clustering.silhouette import Silhouette
from DashAI.back.models.scikit_learn.kmeans_clustering import KMeansClustering

BLOB_SIZE = 30
N_ROWS = 3 * BLOB_SIZE
BLOBS = {frozenset(range(i * BLOB_SIZE, (i + 1) * BLOB_SIZE)) for i in range(3)}
METRIC_NAMES = {"Silhouette", "DaviesBouldin", "CalinskiHarabasz"}
DEGENERATE_TAIL = (
    "Clustering metrics need at least two clusters, so this run has no result "
    "to report. Adjust the model parameters, for instance a larger eps or a "
    "smaller min_samples for DBSCAN."
)
NUMERIC_SCHEMA = {
    "hours": {"type": "Float", "dtype": "float64"},
    "score": {"type": "Float", "dtype": "float64"},
}


def _blobs_frame() -> pd.DataFrame:
    """Three well separated blobs, in columns of very different scales.

    ``hours`` spans roughly 1 to 11 and ``score`` 0 to 100, which is what makes
    the standardisation observable: a distance computed on the raw columns is
    dominated by ``score``.
    """
    rng = np.random.default_rng(seed=0)
    centres = [(2.0, 10.0), (6.0, 50.0), (10.0, 90.0)]
    rows = []
    for hours, score in centres:
        rows.append(
            pd.DataFrame(
                {
                    "hours": rng.normal(hours, 0.3, BLOB_SIZE),
                    "score": rng.normal(score, 3.0, BLOB_SIZE),
                }
            )
        )
    return pd.concat(rows, ignore_index=True)


def _create_dataset(client: TestClient, csv_path: Path, name: str, schema) -> int:
    """Load a CSV through ``DatasetJob``, the way the conftest builds iris."""
    session_factory = client.app.container["session_factory"]
    with session_factory() as db:
        entry = Dataset(name=name, file_path="")
        db.add(entry)
        db.commit()
        db.refresh(entry)
        DatasetJob(
            job_type="DatasetJob",
            kwargs={
                "dataset_id": entry.id,
                "url": "",
                "params": {
                    "dataloader": "CSVDataLoader",
                    "separator": ",",
                    "name": name,
                    "schema": schema,
                },
                "file_path": csv_path,
            },
            db=db,
        ).run()
        db.refresh(entry)
        return entry.id


def _create_session(
    client: TestClient, dataset_id: int, name: str, input_columns
) -> int:
    """Create a session with the payload the front sends for clustering."""
    response = client.post(
        "/api/v1/model-session/",
        json={
            "dataset_id": dataset_id,
            "task_name": "ClusteringTask",
            "name": name,
            "input_columns": input_columns,
            "output_columns": [],
            "train_metrics": [],
            "validation_metrics": [],
            "test_metrics": [],
            "evaluation_strategy": "FullDatasetEvaluationStrategy",
            "splits": json.dumps({}),
            "preprocessing": [],
        },
    )
    assert response.status_code == 201, response.text
    return response.json()["id"]


def _create_run(client: TestClient, session_id: int, model: str, params) -> int:
    """Create a run with the payload the front sends when HPO is off."""
    response = client.post(
        "/api/v1/run/",
        json={
            "model_session_id": session_id,
            "model_name": model,
            "name": f"{model} run",
            "parameters": params,
            "optimizer_name": "",
            "optimizer_parameters": {},
            "plot_history_path": "",
            "plot_slice_path": "",
            "plot_contour_path": "",
            "plot_importance_path": "",
            "goal_metric": "",
            "description": "",
            "nested": None,
        },
    )
    assert response.status_code == 201, response.text
    return response.json()["id"]


def _get(client: TestClient, model, row_id):
    session_factory = client.app.container["session_factory"]
    with session_factory() as db:
        row = db.get(model, row_id)
        db.expunge(row)
        return row


def _metric_rows(client: TestClient, run_id: int):
    session_factory = client.app.container["session_factory"]
    with session_factory() as db:
        rows = db.query(Metric).filter(Metric.run_id == run_id).all()
        for row in rows:
            db.expunge(row)
        return rows


def _scaled_blobs() -> np.ndarray:
    """The features the clustering is expected to be found and scored in."""
    frame = _blobs_frame()
    return StandardScaler().fit_transform(frame[["hours", "score"]])


def _partition(labels) -> set:
    labels = np.asarray(labels)
    return {frozenset(np.flatnonzero(labels == label)) for label in set(labels)}


@pytest.fixture(scope="module", name="csv_dir")
def fixture_csv_dir(tmp_path_factory) -> Path:
    directory = tmp_path_factory.mktemp("clustering_net")
    _blobs_frame().to_csv(directory / "blobs.csv", index=False)

    with_category = _blobs_frame()
    with_category["group"] = ["a", "b", "c"] * BLOB_SIZE
    with_category.to_csv(directory / "blobs_with_category.csv", index=False)
    return directory


@pytest.fixture(scope="module", name="blobs_dataset_id")
def fixture_blobs_dataset(client: TestClient, csv_dir: Path) -> int:
    return _create_dataset(client, csv_dir / "blobs.csv", "blobs", NUMERIC_SCHEMA)


@pytest.fixture(scope="module", name="session_id")
def fixture_session(client: TestClient, blobs_dataset_id: int) -> int:
    return _create_session(
        client, blobs_dataset_id, "clustering net", ["hours", "score"]
    )


@pytest.fixture(name="statuses")
def fixture_statuses(monkeypatch) -> list:
    """Every status transition a run goes through, in order."""
    seen = []
    for name in (
        "set_status_as_delivered",
        "set_status_as_started",
        "set_status_as_finished",
        "set_status_as_error",
    ):
        original = getattr(Run, name)

        def recorder(self, _original=original, _name=name):
            seen.append(_name.removeprefix("set_status_as_"))
            return _original(self)

        monkeypatch.setattr(Run, name, recorder)
    return seen


def _train(client: TestClient, session_id: int, model: str, params) -> int:
    run_id = _create_run(client, session_id, model, params)
    ModelJob(run_id=run_id).run()
    return run_id


def _train_expecting_error(client, session_id, model, params) -> tuple:
    run_id = _create_run(client, session_id, model, params)
    with pytest.raises(JobError) as raised:
        ModelJob(run_id=run_id).run()
    return run_id, str(raised.value)


# --------------------------------------------------------------------------- #
# The session
# --------------------------------------------------------------------------- #


def test_the_session_is_stored_as_the_front_sent_it(client, session_id):
    session = _get(client, ModelSession, session_id)

    assert session.task_name == "ClusteringTask"
    assert session.input_columns == ["hours", "score"]
    assert session.output_columns == []
    assert session.train_metrics == []
    assert session.validation_metrics == []
    assert session.test_metrics == []
    assert session.evaluation_strategy == "FullDatasetEvaluationStrategy"
    assert json.loads(session.splits) == {}
    assert session.preprocessing_status == "ready"
    assert session.preprocessing_job_id is None


# --------------------------------------------------------------------------- #
# A successful run
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    ("model", "params"),
    [
        ("KMeansClustering", {"n_clusters": 3, "random_state": 0}),
        ("AgglomerativeClustering", {"n_clusters": 3}),
        ("DBSCANClustering", {"eps": 0.5, "min_samples": 5}),
    ],
    ids=["kmeans", "agglomerative", "dbscan"],
)
def test_a_run_finishes_and_recovers_the_three_blobs(
    client, session_id, statuses, model, params
):
    run_id = _train(client, session_id, model, params)
    run = _get(client, Run, run_id)

    assert statuses == ["started", "finished"]
    assert run.status == RunStatus.FINISHED
    assert run.start_time is not None
    assert run.end_time is not None

    # Nothing is held out, searched or plotted.
    assert run.split_indexes is None
    assert run.plot_history_path is None
    assert run.plot_slice_path is None
    assert run.plot_contour_path is None
    assert run.plot_importance_path is None
    assert run.parameters == params
    assert run.optimizer_name == ""
    assert run.goal_metric == ""

    # The model is saved under the run, and it is the one that found the blobs.
    assert run.run_path is not None
    assert run.run_path.endswith(str(run_id))
    assert os.path.exists(run.run_path)
    component_registry = client.app.container["component_registry"]
    model_class = component_registry[model]["class"]
    labels = model_class.load(run.run_path).get_cluster_labels()
    assert _partition(labels) == BLOBS


def test_a_run_leaves_the_session_untouched(client, session_id):
    before = _get(client, ModelSession, session_id)
    _train(client, session_id, "KMeansClustering", {"n_clusters": 3})
    after = _get(client, ModelSession, session_id)

    for column in (
        "input_columns",
        "output_columns",
        "train_metrics",
        "validation_metrics",
        "test_metrics",
        "evaluation_strategy",
        "splits",
    ):
        assert getattr(after, column) == getattr(before, column), column


def test_a_run_writes_one_full_last_row_per_clustering_metric(client, session_id):
    run_id = _train(
        client, session_id, "KMeansClustering", {"n_clusters": 3, "random_state": 0}
    )
    rows = _metric_rows(client, run_id)

    assert {row.name for row in rows} == METRIC_NAMES
    assert len(rows) == len(METRIC_NAMES)
    for row in rows:
        assert row.split == SplitEnum.FULL
        assert row.level == LevelEnum.LAST
        assert row.step == 0
        assert row.fold_index is None
        assert row.inner_fold_index is None
        assert row.std_value is None


def test_the_metrics_are_scored_on_the_standardised_features(client, session_id):
    """The values match sklearn on the scaled columns, and only on those.

    The reference is computed here from scratch: centre and scale every column
    with variance, then score the labels the saved model holds. A run that
    scored the raw columns would give different numbers.
    """
    run_id = _train(
        client, session_id, "KMeansClustering", {"n_clusters": 3, "random_state": 0}
    )
    run = _get(client, Run, run_id)
    labels = KMeansClustering.load(run.run_path).get_cluster_labels()
    scaled = _scaled_blobs()

    expected = {
        "Silhouette": silhouette_score(scaled, labels),
        "DaviesBouldin": davies_bouldin_score(scaled, labels),
        "CalinskiHarabasz": calinski_harabasz_score(scaled, labels),
    }
    stored = {row.name: row.value for row in _metric_rows(client, run_id)}

    assert stored == pytest.approx(expected, rel=1e-9)

    raw = _blobs_frame()[["hours", "score"]].to_numpy()
    assert stored["CalinskiHarabasz"] != pytest.approx(
        calinski_harabasz_score(raw, labels), rel=1e-6
    )


def test_training_the_same_run_again_replaces_the_values(client, session_id):
    run_id = _train(
        client, session_id, "KMeansClustering", {"n_clusters": 3, "random_state": 0}
    )
    first = {row.name: row.value for row in _metric_rows(client, run_id)}

    session_factory = client.app.container["session_factory"]
    with session_factory() as db:
        for row in db.query(Metric).filter(Metric.run_id == run_id).all():
            row.value = -999.0
        db.commit()

    ModelJob(run_id=run_id).run()
    rows = _metric_rows(client, run_id)

    assert len(rows) == len(METRIC_NAMES)
    assert {row.name: row.value for row in rows} == pytest.approx(first)
    assert all(row.step == 0 for row in rows)


# --------------------------------------------------------------------------- #
# Runs that fail while training
# --------------------------------------------------------------------------- #


def _assert_failed_without_result(client, run_id, statuses, expected_statuses):
    run = _get(client, Run, run_id)
    assert statuses == expected_statuses
    assert run.status == RunStatus.ERROR
    assert run.run_path is None
    assert _metric_rows(client, run_id) == []


def test_a_run_where_every_point_is_noise_fails(client, session_id, statuses):
    run_id, message = _train_expecting_error(
        client, session_id, "DBSCANClustering", {"eps": 0.5, "min_samples": 1000}
    )

    assert message == (
        "Model training and evaluation failed DBSCANClustering produced 0 "
        f"cluster(s) over {N_ROWS} samples, {N_ROWS} of them labelled as noise. "
        + DEGENERATE_TAIL
    )
    _assert_failed_without_result(client, run_id, statuses, ["started", "error"])


def test_a_run_that_finds_a_single_cluster_fails(client, session_id, statuses):
    run_id, message = _train_expecting_error(
        client, session_id, "DBSCANClustering", {"eps": 100.0, "min_samples": 5}
    )

    assert message == (
        "Model training and evaluation failed DBSCANClustering produced 1 "
        f"cluster(s) over {N_ROWS} samples, 0 of them labelled as noise. "
        + DEGENERATE_TAIL
    )
    _assert_failed_without_result(client, run_id, statuses, ["started", "error"])


def test_a_run_with_one_cluster_per_point_fails(client, session_id, statuses):
    run_id, message = _train_expecting_error(
        client, session_id, "AgglomerativeClustering", {"n_clusters": N_ROWS}
    )

    assert message == (
        f"Model training and evaluation failed AgglomerativeClustering produced "
        f"{N_ROWS} cluster(s) over {N_ROWS} samples, 0 of them labelled as "
        "noise. " + DEGENERATE_TAIL
    )
    _assert_failed_without_result(client, run_id, statuses, ["started", "error"])


def test_a_model_that_fails_to_train_is_reported(
    client, session_id, statuses, monkeypatch
):
    def fail(self, *args, **kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr(KMeansClustering, "train", fail)
    run_id, message = _train_expecting_error(
        client, session_id, "KMeansClustering", {"n_clusters": 3}
    )

    assert message == (
        "Model training and evaluation failed Model training failed boom"
    )
    _assert_failed_without_result(client, run_id, statuses, ["started", "error"])


def test_a_metric_that_fails_is_reported_and_nothing_is_written(
    client, session_id, statuses, monkeypatch
):
    def fail(x, labels):
        raise RuntimeError("boom")

    monkeypatch.setattr(Silhouette, "score", staticmethod(fail))
    run_id, message = _train_expecting_error(
        client, session_id, "KMeansClustering", {"n_clusters": 3}
    )

    assert message == (
        "Model training and evaluation failed Metric calculation failed boom"
    )
    _assert_failed_without_result(client, run_id, statuses, ["started", "error"])


# --------------------------------------------------------------------------- #
# Runs that fail before training starts
# --------------------------------------------------------------------------- #


def test_an_unknown_model_is_reported_before_the_run_starts(
    client, session_id, statuses
):
    session_factory = client.app.container["session_factory"]
    with session_factory() as db:
        run = Run(
            model_session_id=session_id,
            model_name="NotAClusteringModel",
            parameters={},
            optimizer_name="",
            optimizer_parameters={},
            goal_metric="",
            name="unknown model run",
        )
        db.add(run)
        db.commit()
        run_id = run.id

    with pytest.raises(JobError) as raised:
        ModelJob(run_id=run_id).run()

    assert str(raised.value) == (
        f"Error preparing dataset and components for run {run_id}: "
        "Unable to find Model with name NotAClusteringModel in registry."
    )
    _assert_failed_without_result(client, run_id, statuses, ["error"])


def test_a_dataset_missing_from_disk_is_reported(client, csv_dir, statuses):
    dataset_id = _create_dataset(
        client, csv_dir / "blobs.csv", "blobs to delete", NUMERIC_SCHEMA
    )
    session_id = _create_session(
        client, dataset_id, "clustering net, deleted", ["hours", "score"]
    )
    run_id = _create_run(client, session_id, "KMeansClustering", {"n_clusters": 3})
    file_path = _get(client, Dataset, dataset_id).file_path
    shutil.rmtree(file_path)

    with pytest.raises(JobError) as raised:
        ModelJob(run_id=run_id).run()

    assert str(raised.value) == (
        f"Error preparing dataset and components for run {run_id}: "
        f"Can not load dataset from path {file_path}"
    )
    _assert_failed_without_result(client, run_id, statuses, ["error"])


def test_a_dataset_the_task_cannot_take_is_reported(client, csv_dir, statuses):
    """A categorical input column: ``ClusteringTask`` only takes numbers."""
    dataset_id = _create_dataset(
        client,
        csv_dir / "blobs_with_category.csv",
        "blobs with category",
        {**NUMERIC_SCHEMA, "group": {"type": "Categorical", "dtype": "string"}},
    )
    session_id = _create_session(
        client, dataset_id, "clustering net, category", ["hours", "score", "group"]
    )
    run_id = _create_run(client, session_id, "KMeansClustering", {"n_clusters": 3})

    with pytest.raises(JobError) as raised:
        ModelJob(run_id=run_id).run()

    assert str(raised.value) == (
        f"Error preparing the dataset for run {run_id}: "
        f"Can not prepare Dataset {dataset_id} for Task ClusteringTask"
    )
    _assert_failed_without_result(client, run_id, statuses, ["error"])


# --------------------------------------------------------------------------- #
# Prediction and explanation
# --------------------------------------------------------------------------- #


NO_OUTPUT_COLUMNS = "Model session has no output columns configured"


def _predictions_on_disk(client: TestClient) -> set:
    path = Path(client.app.container["config"]["DATASETS_PATH"]) / "predictions"
    return set(os.listdir(path)) if path.exists() else set()


def test_predicting_with_a_clustering_run_creates_no_prediction(
    client, session_id, blobs_dataset_id
):
    """What survives fixing the job's exception type: no result, ERROR, the text.

    The exception class and its status code are deliberately not asserted: a
    job should raise ``JobError``, and this one does not yet.
    """
    run_id = _train(client, session_id, "KMeansClustering", {"n_clusters": 3})
    response = client.post(
        "/api/v1/predict/", json={"run_id": run_id, "dataset_id": blobs_dataset_id}
    )
    assert response.status_code == 200, response.text
    prediction_id = response.json()["id"]
    before = _predictions_on_disk(client)

    with pytest.raises(Exception, match=NO_OUTPUT_COLUMNS) as raised:
        PredictJob(prediction_id=prediction_id).run()

    error = raised.value
    assert (getattr(error, "detail", None) or str(error)) == NO_OUTPUT_COLUMNS

    prediction = _get(client, Prediction, prediction_id)
    assert prediction.status == PredictionStatus.ERROR
    assert prediction.results_path is None
    assert _predictions_on_disk(client) == before


def test_the_prediction_preview_refuses_a_clustering_run(client, session_id):
    run_id = _train(client, session_id, "KMeansClustering", {"n_clusters": 3})

    response = client.post(
        "/api/v1/predict/preview",
        data={
            "run_id": str(run_id),
            "manual_input_data": json.dumps([{"hours": 2.0, "score": 10.0}]),
        },
    )

    assert response.status_code == 422
    assert response.json()["detail"] == NO_OUTPUT_COLUMNS


@pytest.mark.parametrize("explainer_type", ["GlobalExplainer", "LocalExplainer"])
def test_no_explainer_is_offered_for_clustering(client, explainer_type):
    response = client.get(
        "/api/v1/component/",
        params={
            "select_types": [explainer_type],
            "related_component": "ClusteringTask",
        },
    )

    assert response.status_code == 200, response.text
    assert response.json() == []
