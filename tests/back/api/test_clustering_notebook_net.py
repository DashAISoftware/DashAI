"""End-to-end regression net for clustering inside a notebook.

The ``Clustering`` converter appends a cluster label column to the notebook's
dataset and leaves a report next to it; the clustering explorers read that
report to draw. Written against ``feat/clustering-units`` before ``ConverterJob``
and ``ExplorerJob`` are merged with their unit versions, so the merge has
something to be measured against. Only what a user sees is asserted: the
statuses, the dataset on disk, the report file and the exact error texts.
"""

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from fastapi.testclient import TestClient
from sklearn.cluster import KMeans
from sklearn.metrics import (
    calinski_harabasz_score,
    davies_bouldin_score,
    silhouette_score,
)

from DashAI.back.core.enums.status import ConverterStatus, ExplorerStatus
from DashAI.back.dataloaders.classes.dashai_dataset import load_dataset
from DashAI.back.dependencies.database.models import (
    Converter,
    Dataset,
    Explorer,
)
from DashAI.back.job.base_job import JobError
from DashAI.back.job.converter_job import ConverterJob
from DashAI.back.job.dataset_job import DatasetJob
from DashAI.back.job.explorer_job import ExplorerJob

IRIS_NUMERIC = ["SepalLengthCm", "SepalWidthCm", "PetalLengthCm", "PetalWidthCm"]
KMEANS = {
    "algorithm": "KMeansClustering",
    "algorithm_params": {"n_clusters": 3, "random_state": 0},
    "output_column_name": "cluster",
}
AGGLOMERATIVE = {
    "algorithm": "AgglomerativeClustering",
    "algorithm_params": {"n_clusters": 3},
    "output_column_name": "cluster",
}


@pytest.fixture(name="notebook")
def create_notebook(client: TestClient, dataset_1):
    response = client.post(
        "/api/v1/notebook/",
        json={"dataset_id": dataset_1.id, "name": "clustering notebook net"},
    )
    assert response.status_code == 201, response.text
    return response.json()


def _create_converter(client, notebook_id, converter, params, scope=None) -> int:
    response = client.post(
        "/api/v1/converter/",
        json={
            "notebook_id": notebook_id,
            "converter": converter,
            "parameters": {
                "order": 0,
                "params": params,
                "scope": scope if scope is not None else {"columns": [], "rows": []},
                "target": None,
            },
        },
    )
    assert response.status_code == 201, response.text
    return response.json()["id"]


def _run_clustering(client, notebook, params=None) -> int:
    converter_id = _create_converter(
        client, notebook["id"], "Clustering", params or KMEANS
    )
    ConverterJob(converter_id=converter_id).run()
    return converter_id


def _converter_status(client, converter_id):
    session_factory = client.app.container["session_factory"]
    with session_factory() as db:
        return db.get(Converter, converter_id).status


def _report_path(client, notebook, converter_id) -> Path:
    notebook_path = Path(client.app.container["config"]["NOTEBOOK_PATH"])
    return (
        notebook_path
        / str(notebook["id"])
        / "converters"
        / str(converter_id)
        / "report.json"
    )


def _notebook_frame(notebook) -> pd.DataFrame:
    return load_dataset(f"{notebook['file_path']}/dataset").to_pandas()


def _iris_numeric(client, dataset_1) -> np.ndarray:
    frame = load_dataset(f"{dataset_1.file_path}/dataset").to_pandas()
    return frame[IRIS_NUMERIC].to_numpy()


def _create_explorer(client, notebook_id, exploration_type, columns, params) -> int:
    """Written straight to the database: the explorer's own checks are the
    subject here, not the endpoint's column validation."""
    session_factory = client.app.container["session_factory"]
    with session_factory() as db:
        explorer = Explorer(
            notebook_id=notebook_id,
            exploration_type=exploration_type,
            columns=[{"columnName": name} for name in columns],
            parameters=params,
            name=exploration_type,
        )
        db.add(explorer)
        db.commit()
        return explorer.id


def _explorer(client, explorer_id):
    session_factory = client.app.container["session_factory"]
    with session_factory() as db:
        row = db.get(Explorer, explorer_id)
        db.expunge(row)
        return row


# --------------------------------------------------------------------------- #
# The converter
# --------------------------------------------------------------------------- #


def test_the_converter_appends_the_kmeans_labels(client, notebook, dataset_1):
    converter_id = _run_clustering(client, notebook)

    assert _converter_status(client, converter_id) == ConverterStatus.FINISHED

    frame = _notebook_frame(notebook)
    assert list(frame.columns) == [*IRIS_NUMERIC, "Species", "cluster"]
    assert str(frame["cluster"].dtype) == "int64"

    expected = KMeans(n_clusters=3, random_state=0).fit_predict(
        _iris_numeric(client, dataset_1)
    )
    assert frame["cluster"].tolist() == expected.tolist()


def test_the_converter_leaves_a_report_of_the_fit(client, notebook, dataset_1):
    converter_id = _run_clustering(client, notebook)
    report = json.loads(_report_path(client, notebook, converter_id).read_text())

    raw = _iris_numeric(client, dataset_1)
    labels = KMeans(n_clusters=3, random_state=0).fit_predict(raw)
    sizes = dict(zip(*np.unique(labels, return_counts=True), strict=True))

    assert report["converter"] == "Clustering"
    assert report["algorithm"] == "KMeansClustering"
    assert report["algorithm_key"] == "kmeans"
    assert report["cluster_column"] == "cluster"
    assert report["n_clusters"] == 3
    assert report["feature_columns"] == IRIS_NUMERIC
    assert report["cluster_sizes"] == {
        str(label): int(count) for label, count in sizes.items()
    }
    # Scored on the raw numeric columns, unlike a model session.
    assert report["metrics"] == pytest.approx(
        {
            "Silhouette": silhouette_score(raw, labels),
            "DaviesBouldin": davies_bouldin_score(raw, labels),
            "CalinskiHarabasz": calinski_harabasz_score(raw, labels),
        },
        rel=1e-9,
    )
    assert set(report["fit_attributes"]) == {"cluster_centers", "inertia"}
    assert [
        (profile["cluster"], profile["size"]) for profile in report["cluster_profiles"]
    ] == [(int(label), int(count)) for label, count in sizes.items()]


def test_a_second_run_does_not_overwrite_the_first_label_column(client, notebook):
    _run_clustering(client, notebook)
    second = _run_clustering(client, notebook)

    assert _converter_status(client, second) == ConverterStatus.FINISHED
    assert list(_notebook_frame(notebook).columns) == [
        *IRIS_NUMERIC,
        "Species",
        "cluster",
        "cluster_1",
    ]


def test_a_scope_without_numeric_columns_is_refused(client, notebook, dataset_1):
    converter_id = _create_converter(
        client,
        notebook["id"],
        "Clustering",
        KMEANS,
        scope={"columns": [{"idx": 5}], "rows": []},
    )

    with pytest.raises(JobError) as raised:
        ConverterJob(converter_id=converter_id).run()

    assert str(raised.value) == (
        f"Error applying converters to dataset {dataset_1.id}: "
        "Validation error fitting Clustering: Clustering requires at least one "
        "numeric column to fit."
    )
    assert _converter_status(client, converter_id) == ConverterStatus.ERROR
    assert not _report_path(client, notebook, converter_id).exists()


@pytest.fixture(name="notebook_with_nan")
def create_notebook_with_nan(client: TestClient, tmp_path):
    csv_path = tmp_path / "with_nan.csv"
    # Enough distinct values for both columns to load as Float: a short
    # column with a gap is inferred as categorical and never reaches the fit.
    rng = np.random.default_rng(seed=0)
    frame = pd.DataFrame({"a": rng.normal(size=40), "b": rng.normal(size=40)})
    frame.loc[3, "a"] = None
    frame.to_csv(csv_path, index=False)

    session_factory = client.app.container["session_factory"]
    with session_factory() as db:
        entry = Dataset(name="clustering with nan", file_path="")
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
                    "name": entry.name,
                    "schema": {
                        "a": {"type": "Float", "dtype": "float64"},
                        "b": {"type": "Float", "dtype": "float64"},
                    },
                },
                "file_path": csv_path,
            },
            db=db,
        ).run()
        dataset_id = entry.id

    response = client.post(
        "/api/v1/notebook/",
        json={"dataset_id": dataset_id, "name": "clustering nan net"},
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_missing_values_are_refused(client, notebook_with_nan):
    params = {**KMEANS, "algorithm_params": {"n_clusters": 2, "random_state": 0}}
    converter_id = _create_converter(
        client, notebook_with_nan["id"], "Clustering", params
    )

    with pytest.raises(JobError) as raised:
        ConverterJob(converter_id=converter_id).run()

    assert str(raised.value) == (
        f"Error applying converters to dataset {notebook_with_nan['dataset_id']}: "
        "Validation error fitting Clustering: Clustering input contains NaN "
        "values in the numeric columns used for clustering."
    )
    assert _converter_status(client, converter_id) == ConverterStatus.ERROR


# --------------------------------------------------------------------------- #
# The explorers
# --------------------------------------------------------------------------- #


def test_a_clustering_explorer_draws_from_the_converter_report(client, notebook):
    _run_clustering(client, notebook)
    explorer_id = _create_explorer(
        client,
        notebook["id"],
        "ClusteringScatterExplorer",
        IRIS_NUMERIC,
        {"reduction_method": "pca"},
    )

    ExplorerJob(explorer_id=explorer_id).run()

    explorer = _explorer(client, explorer_id)
    assert explorer.status == ExplorerStatus.FINISHED
    assert explorer.exploration_path
    assert Path(explorer.exploration_path).exists()


def _explore_expecting_error(client, notebook_id, exploration_type, columns, params):
    explorer_id = _create_explorer(
        client, notebook_id, exploration_type, columns, params
    )
    with pytest.raises(JobError) as raised:
        ExplorerJob(explorer_id=explorer_id).run()
    assert _explorer(client, explorer_id).status == ExplorerStatus.ERROR
    return str(raised.value)


def test_an_explorer_without_a_finished_converter_is_refused(client, notebook):
    message = _explore_expecting_error(
        client,
        notebook["id"],
        "ClusteringScatterExplorer",
        IRIS_NUMERIC,
        {"reduction_method": "pca"},
    )

    assert message == (
        "This explorer requires a converter report, but the notebook has no "
        "finished converters of type 'Clustering'."
    )


def test_an_explorer_after_another_converter_is_refused(client, notebook):
    _run_clustering(client, notebook)
    other = _create_converter(
        client,
        notebook["id"],
        "ColumnRemover",
        {},
        scope={"columns": [{"idx": 5}], "rows": []},
    )
    ConverterJob(converter_id=other).run()
    assert _converter_status(client, other) == ConverterStatus.FINISHED

    message = _explore_expecting_error(
        client,
        notebook["id"],
        "ClusteringScatterExplorer",
        IRIS_NUMERIC,
        {"reduction_method": "pca"},
    )

    assert message == (
        "This explorer requires a report from the most recently finished "
        "converter in the notebook, but the last converter was 'ColumnRemover', "
        "not 'Clustering'. Re-run the 'Clustering' converter before creating "
        "this explorer so its report reflects the current dataset."
    )


def test_an_explorer_for_another_algorithm_is_refused(client, notebook):
    _run_clustering(client, notebook)

    message = _explore_expecting_error(
        client, notebook["id"], "DendrogramExplorer", [], {}
    )

    assert message == (
        "This explorer requires the 'agglomerative' clustering algorithm, but the "
        "last Clustering converter ran 'kmeans'. Re-run the Clustering converter "
        "selecting the 'agglomerative' algorithm."
    )


def test_the_algorithm_an_explorer_requires_is_accepted(client, notebook):
    _run_clustering(client, notebook, AGGLOMERATIVE)
    explorer_id = _create_explorer(client, notebook["id"], "DendrogramExplorer", [], {})

    ExplorerJob(explorer_id=explorer_id).run()

    assert _explorer(client, explorer_id).status == ExplorerStatus.FINISHED


def test_an_explorer_whose_report_is_gone_is_refused(client, notebook):
    converter_id = _run_clustering(client, notebook)
    _report_path(client, notebook, converter_id).unlink()

    message = _explore_expecting_error(
        client,
        notebook["id"],
        "ClusteringScatterExplorer",
        IRIS_NUMERIC,
        {"reduction_method": "pca"},
    )

    assert message == (
        "This explorer requires a converter report, but the latest finished "
        "'Clustering' converter did not produce one."
    )
