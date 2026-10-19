"""The target-free training chain, run as a graph.

``ModelJob`` trains a clustering session through six units, and the claim that
the same six make a graph the engine accepts -- none of the new ones declares a
runtime param the engine cannot supply -- was written down before anyone ran
it. This runs it, on the blobs of the clustering regression net.

    load  --dataset, dataset_id-->  prep
    prep  --n_labels, task_name-->  build
    prep  --features------------->  fit      build --model-->  fit
    prep  --features------------->  score    fit   --model-->  score
                                             fit   --model-->  save

The pipeline is a sandbox, as the supervised one is: no Run, no ModelSession,
and the scores live in a ``NodeArtifact`` rather than in ``Metric`` rows.
"""

import os

import numpy as np
import pytest
from fastapi.testclient import TestClient
from sklearn.metrics import (
    calinski_harabasz_score,
    davies_bouldin_score,
    silhouette_score,
)

from DashAI.back.core.enums.status import NodeRunStatus, PipelineRunStatus
from DashAI.back.dag import validate
from DashAI.back.dag.expand import expand
from DashAI.back.dependencies.database.models import (
    Metric,
    ModelSession,
    NodeArtifact,
    Pipeline,
    PipelineRun,
    Run,
)
from DashAI.back.job.pipeline_job import PipelineJob
from DashAI.back.models.scikit_learn.kmeans_clustering import KMeansClustering
from tests.back.api.test_model_job_clustering_net import (
    BLOBS,
    _blobs_frame,
    _partition,
    _scaled_blobs,
    fixture_blobs_dataset,  # noqa: F401
    fixture_csv_dir,  # noqa: F401
)

METRICS = ["Silhouette", "DaviesBouldin", "CalinskiHarabasz"]

#: What each of the seven drawn edges carries once expanded: nine wires.
#: ``features`` reaches the fit and the score straight from the preparation,
#: skipping the build, which never needed the data.
EXPECTED_WIRES = {
    ("load", "prep"): {"dataset", "dataset_id"},
    ("prep", "build"): {"n_labels", "task_name"},
    ("prep", "fit"): {"features"},
    ("build", "fit"): {"model"},
    ("prep", "score"): {"features"},
    ("fit", "score"): {"model"},
    ("fit", "save"): {"model"},
}


def _target_free_blocks(dataset_id: int):
    """The six blocks of a clustering run, and the seven edges between them."""
    configs = {
        "load": ("LoadDatasetUnit", {"dataset_id": dataset_id}),
        "prep": (
            "PrepareWithoutTargetUnit",
            {
                "task_name": "ClusteringTask",
                "input_columns": ["hours", "score"],
                "standardise": True,
            },
        ),
        "build": (
            "BuildModelUnit",
            {
                "model": {
                    "component": "KMeansClustering",
                    "params": {"n_clusters": 3, "random_state": 0},
                },
                "train_metrics": [],
                "validation_metrics": [],
                "test_metrics": [],
            },
        ),
        "fit": ("FitWithoutTargetUnit", {}),
        "score": ("ScoreClustersUnit", {"metrics": METRICS}),
        "save": ("SaveModelUnit", {}),
    }
    steps = [
        {"id": node_id, "units": [{"id": node_id, "unit": unit, "config": config}]}
        for node_id, (unit, config) in configs.items()
    ]
    edges = [{"source": source, "target": target} for source, target in EXPECTED_WIRES]
    return steps, edges


def _carried(wires) -> dict:
    """``{(source, target): keys}`` from ``(source, target, key)`` triples."""
    carried = {}
    for source, target, key in wires:
        carried.setdefault((source, target), set()).add(key)
    return carried


def test_the_chain_is_a_graph_the_engine_accepts(blobs_dataset_id):
    """Validated statically, before any unit runs.

    The validator rejects a node whose runtime params nothing supplies, so a
    graph that validates is the proof that the three target-free units are
    usable as nodes. Their configuration also comes out of the expansion as it
    went in: the engine only fills ``run_id`` and ``artifact_prefix``, and none
    of them takes either.
    """
    steps, edges = _target_free_blocks(blobs_dataset_id)
    graph = expand(steps, edges, pipeline_run_id=1)

    order = validate(graph)

    position = {node_id: index for index, node_id in enumerate(order)}
    assert set(position) == {"load", "prep", "build", "fit", "score", "save"}
    assert position["load"] < position["prep"] < position["build"] < position["fit"]
    assert position["fit"] < position["score"]
    assert position["fit"] < position["save"]

    assert len(graph.edges) == 9
    assert all(edge.src_key == edge.dst_key for edge in graph.edges)
    wires = [(edge.src, edge.dst, edge.src_key) for edge in graph.edges]
    assert _carried(wires) == EXPECTED_WIRES

    stored = {step["id"]: step["units"][0]["config"] for step in steps}
    for node_id in ("prep", "fit", "score"):
        assert dict(graph.node(node_id).config) == stored[node_id], node_id
    assert graph.node("build").config["run_id"] is None
    assert graph.node("save").config["artifact_prefix"] == "pipeline-1-save"


@pytest.fixture(name="finished_pipeline_run", scope="module")
def run_the_graph(client: TestClient, blobs_dataset_id: int):
    session_factory = client.app.container["session_factory"]
    steps, edges = _target_free_blocks(blobs_dataset_id)

    with session_factory() as db:
        pipeline = Pipeline(name="Clustering as a graph", steps=steps, edges=edges)
        db.add(pipeline)
        db.commit()
        pipeline_id = pipeline.id

    PipelineJob(pipeline_id=pipeline_id).run()

    with session_factory() as db:
        pipeline_run = db.query(PipelineRun).filter_by(pipeline_id=pipeline_id).one()
        db.refresh(pipeline_run)
        # Read everything now: the session closes with the fixture.
        yield {
            "id": pipeline_run.id,
            "status": pipeline_run.status,
            "error_message": pipeline_run.error_message,
            "edges": pipeline_run.edges,
            "nodes": {
                row.node_id: {"status": row.status, "config": row.config}
                for row in pipeline_run.node_runs
            },
            "artifacts": {
                (row.node_run.node_id, row.key): row.value
                for row in db.query(NodeArtifact).all()
            },
        }


def test_the_whole_graph_runs_to_completion(finished_pipeline_run):
    assert finished_pipeline_run["status"] == PipelineRunStatus.FINISHED
    assert finished_pipeline_run["error_message"] is None

    nodes = finished_pipeline_run["nodes"]
    assert set(nodes) == {"load", "prep", "build", "fit", "score", "save"}
    for node_id, node in nodes.items():
        assert node["status"] == NodeRunStatus.FINISHED, node_id

    # The run froze the wiring it executed, and it is the one validated above.
    frozen = [
        (edge["src"], edge["dst"], edge["src_key"])
        for edge in finished_pipeline_run["edges"]
    ]
    assert _carried(frozen) == EXPECTED_WIRES


def test_the_scores_live_in_an_artifact(finished_pipeline_run):
    """The numbers a clustering run writes as FULL rows, kept as an artifact.

    Checked against sklearn on the standardised columns, with the labels of
    the model the graph saved, and only on those: the raw columns give a
    different score, so a graph that skipped the scaling would show here.
    """
    artifacts = finished_pipeline_run["artifacts"]
    model = KMeansClustering.load(artifacts[("save", "model_path")])
    labels = model.get_cluster_labels()
    scaled = _scaled_blobs()

    expected = {
        "Silhouette": silhouette_score(scaled, labels),
        "DaviesBouldin": davies_bouldin_score(scaled, labels),
        "CalinskiHarabasz": calinski_harabasz_score(scaled, labels),
    }
    scores = artifacts[("score", "metrics")]
    assert scores == {"full": pytest.approx(expected, rel=1e-9)}

    raw = _blobs_frame()[["hours", "score"]].to_numpy()
    assert scores["full"]["CalinskiHarabasz"] != pytest.approx(
        calinski_harabasz_score(raw, labels), rel=1e-6
    )


def test_the_model_is_saved_where_no_real_run_could_collide_with_it(
    client, finished_pipeline_run
):
    model_path = finished_pipeline_run["artifacts"][("save", "model_path")]
    runs_path = str(client.app.container["config"]["RUNS_PATH"])

    assert model_path.startswith(runs_path)
    assert os.path.exists(model_path)
    assert os.path.basename(model_path) == (
        f"pipeline-{finished_pipeline_run['id']}-save"
    )

    # And it is the model that was fitted: it found the three blobs.
    labels = np.asarray(KMeansClustering.load(model_path).get_cluster_labels())
    assert _partition(labels) == BLOBS


def test_only_the_serializable_outputs_are_recorded(finished_pipeline_run):
    """References become artifacts; the live features and model do not."""
    recorded = set(finished_pipeline_run["artifacts"])

    assert recorded == {
        ("load", "dataset_id"),
        ("load", "dataset_path"),
        ("prep", "task_name"),
        ("build", "model_parameters"),
        ("score", "metrics"),
        ("save", "model_path"),
    }


def test_the_sandbox_creates_no_run_and_writes_no_rows(client, finished_pipeline_run):
    """No Run, no ModelSession, no Metric rows, and a build with no run.

    Weaker than its supervised counterpart in ``test_model_job_as_a_graph.py``:
    no clustering model logs metrics while it trains, and the scoring unit
    writes nothing by contract, so the empty Metric table is not a model being
    stopped. What it does pin is that the rows a clustering job writes are the
    job's: run as a graph, the same chain leaves them out.
    """
    assert finished_pipeline_run["nodes"]["build"]["config"]["run_id"] is None

    session_factory = client.app.container["session_factory"]
    with session_factory() as db:
        assert db.query(Run).count() == 0
        assert db.query(ModelSession).count() == 0
        assert db.query(Metric).count() == 0
