"""ModelJob's whole shape, run as a graph. The test that says the design works.

The spike that established the engine never ran this, and the three problems it
left open all live here: where run_id goes, whether the bundling rule survives
fifteen edges, and whether a training pipeline can produce metrics with no Run
row to hang them on.

Six nodes, and the pipeline is a sandbox: it creates no Run and no ModelSession,
writes no Metric rows, and keeps its model out of the way of every real run's.

    load --dataset,dataset_id--> prep --x,y,n_labels,task_name--> build
                                  |                                |
                                  +-------x,y,task-------------> fit <-+
                                                                  |
                                              +-------model-------+-------+
                                              v                           v
                                            eval                        save
"""

import json
import os

import joblib
import pytest
from datasets import ClassLabel, Value
from fastapi.testclient import TestClient

from DashAI.back.core.enums.metrics import LevelEnum, SplitEnum
from DashAI.back.core.enums.status import NodeRunStatus, PipelineRunStatus
from DashAI.back.dataloaders.classes.csv_dataloader import CSVDataLoader
from DashAI.back.dependencies.database.models import (
    Dataset,
    Metric,
    ModelSession,
    NodeArtifact,
    NodeRun,
    Pipeline,
    PipelineRun,
    Run,
)
from DashAI.back.dependencies.registry import ComponentRegistry
from DashAI.back.job.base_job import JobError
from DashAI.back.job.pipeline_job import PipelineJob
from DashAI.back.metrics.base_metric import BaseMetric
from DashAI.back.models.base_model import BaseModel
from DashAI.back.optimizers.optuna_optimizer import OptunaOptimizer
from DashAI.back.splitters.holdout import HoldoutSplitter
from DashAI.back.tasks.base_task import BaseTask
from DashAI.back.units.build_model_unit import BuildModelUnit
from DashAI.back.units.evaluate_model_to_artifact_unit import (
    EvaluateModelToArtifactUnit,
)
from DashAI.back.units.fit_model_unit import FitModelUnit
from DashAI.back.units.load_dataset_unit import LoadDatasetUnit
from DashAI.back.units.prepare_and_split_unit import PrepareAndSplitUnit
from DashAI.back.units.save_model_unit import SaveModelUnit

SPLITTER = {
    "component": "HoldoutSplitter",
    "params": {
        "train": 0.5,
        "test": 0.2,
        "validation": 0.3,
        "shuffle": True,
        "stratify": False,
        "random_state": 42,
    },
}


class GraphTask(BaseTask):
    name: str = "GraphTask"
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


#: How many times a model asked to log metrics while training, across the run.
#: A model instance does not survive to be inspected -- the graph releases it --
#: and the count is what makes "no metric rows" a consequence rather than a
#: coincidence.
LOG_ATTEMPTS = []


class GraphModel(BaseModel):
    """Logs metrics while training, the way the torch-based models do.

    That matters for what this file is testing. A model that never asks to log
    would leave the Metric table empty no matter what the pipeline did, so the
    sandbox would look airtight without being tested at all. This one asks on
    every train call, so an empty Metric table means the switch stopped it.
    """

    COMPATIBLE_COMPONENTS = ["GraphTask"]

    def __init__(self, **kwargs):
        self.trained_with = None

    def save(self, filename):
        joblib.dump({"trained_with": self.trained_with}, filename)

    def load(self, filename):
        return joblib.load(filename)

    def predict(self, x):
        return [0] * x.shape[0]

    def train(self, x_train, y_train, x_validation=None, y_validation=None):
        self.trained_with = {"train": x_train.shape[0]}
        LOG_ATTEMPTS.append(getattr(self, "run_id", "missing"))
        self.calculate_metrics(split=SplitEnum.TRAIN, level=LevelEnum.STEP)
        return self

    def prepare_dataset(self, dataset, is_fit=False):
        return dataset

    def prepare_output(self, dataset, is_fit=False):
        return [0] * len(LOG_ATTEMPTS or [0])


class GraphMetric(BaseMetric):
    COMPATIBLE_COMPONENTS = ["GraphTask"]
    MAXIMIZE = True

    @staticmethod
    def score(true_labels, probs_pred_labels):
        return 0.5


@pytest.fixture(scope="module", name="graph_registry", autouse=True)
def setup_graph_registry(client):
    services = client.app.container._services
    sentinel = object()
    old = services.get("component_registry", sentinel)

    services["component_registry"] = ComponentRegistry(
        initial_components=[
            GraphTask,
            GraphModel,
            GraphMetric,
            CSVDataLoader,
            OptunaOptimizer,
            PipelineJob,
            LoadDatasetUnit,
            PrepareAndSplitUnit,
            HoldoutSplitter,
            BuildModelUnit,
            FitModelUnit,
            EvaluateModelToArtifactUnit,
            SaveModelUnit,
        ]
    )
    yield services["component_registry"]
    if old is sentinel:
        del services["component_registry"]
    else:
        services["component_registry"] = old


def _model_job_blocks(dataset_id: int):
    """The six blocks, and the six drawn edges that stand for fifteen wires."""
    steps = [
        {
            "id": "load",
            "units": [
                {
                    "id": "load",
                    "unit": "LoadDatasetUnit",
                    "config": {"dataset_id": dataset_id},
                }
            ],
        },
        {
            "id": "prep",
            "units": [
                {
                    "id": "prep",
                    "unit": "PrepareAndSplitUnit",
                    "config": {
                        "task_name": "GraphTask",
                        "input_columns": ["SepalLengthCm", "SepalWidthCm"],
                        "output_columns": ["Species"],
                        "splitter": SPLITTER,
                    },
                }
            ],
        },
        {
            "id": "build",
            "units": [
                {
                    "id": "build",
                    "unit": "BuildModelUnit",
                    "config": {
                        "model": {"component": "GraphModel", "params": {}},
                        "train_metrics": ["GraphMetric"],
                        "validation_metrics": ["GraphMetric"],
                        "test_metrics": ["GraphMetric"],
                    },
                }
            ],
        },
        {
            "id": "fit",
            "units": [
                {
                    "id": "fit",
                    "unit": "FitModelUnit",
                    "config": {
                        "optimizer": {
                            "component": "OptunaOptimizer",
                            "params": {},
                        },
                        "goal_metric": "GraphMetric",
                    },
                }
            ],
        },
        {
            "id": "eval",
            "units": [
                {
                    "id": "eval",
                    "unit": "EvaluateModelToArtifactUnit",
                    "config": {"splits": ["TRAIN", "VALIDATION", "TEST"]},
                }
            ],
        },
        {
            "id": "save",
            "units": [{"id": "save", "unit": "SaveModelUnit", "config": {}}],
        },
    ]
    edges = [
        {"source": "load", "target": "prep"},
        {"source": "prep", "target": "build"},
        {"source": "prep", "target": "fit"},
        {"source": "build", "target": "fit"},
        {"source": "fit", "target": "eval"},
        {"source": "fit", "target": "save"},
    ]
    return steps, edges


@pytest.fixture(name="finished_pipeline_run", scope="module")
def run_the_graph(client: TestClient, dataset_1: Dataset, graph_registry):
    session_factory = client.app.container["session_factory"]
    steps, edges = _model_job_blocks(dataset_1.id)

    with session_factory() as db:
        pipeline = Pipeline(name="ModelJob as a graph", steps=steps, edges=edges)
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
            "steps": pipeline_run.steps,
            "edges": pipeline_run.edges,
            "nodes": {
                row.node_id: {
                    "status": row.status,
                    "start_time": row.start_time,
                    "end_time": row.end_time,
                    "block_id": row.block_id,
                    "node_type": row.node_type,
                    "config": row.config,
                }
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
    assert set(nodes) == {"load", "prep", "build", "fit", "eval", "save"}
    for node_id, node in nodes.items():
        assert node["status"] == NodeRunStatus.FINISHED, node_id
        assert node["start_time"] is not None, node_id
        assert node["end_time"] is not None, node_id


def test_six_drawn_edges_expand_into_twelve_wires(finished_pipeline_run):
    """The granularity problem, measured.

    The unit contract is finer than a canvas can draw: FitModelUnit alone
    requires seven keys. One drawn edge carries every key its two units agree
    on, which is what makes six shapes on a canvas enough for this graph.

    It was fifteen while BuildModelUnit still took the data. It stopped taking
    it once a model could be fitted over folds, where the data changes on every
    iteration and binding one partition at construction would leave the metrics
    describing whichever fold happened to be built with. The two wires that
    disappeared are ``x`` and ``y`` from prep to build; whoever fits the model
    points it at the data now.

    The twelfth went when the hyperparameter search stopped being handed the
    task. It was the sixth argument of ``optimize`` while the optimizer fitted
    and scored inline; the objective is now a callable the fitting unit builds,
    so the task is no longer anything the search needs to be told.
    """
    edges = finished_pipeline_run["edges"]
    assert len(edges) == 12

    carried = {}
    for edge in edges:
        carried.setdefault((edge["src"], edge["dst"]), set()).add(edge["src_key"])

    assert carried == {
        ("load", "prep"): {"dataset", "dataset_id"},
        ("prep", "build"): {"n_labels", "task_name"},
        ("prep", "fit"): {"x", "y"},
        ("build", "fit"): {
            "model",
            "factory",
            "optimizable_parameters",
            "model_parameters",
        },
        ("fit", "eval"): {"model"},
        ("fit", "save"): {"model"},
    }


def test_the_sandbox_writes_no_metric_rows(client, finished_pipeline_run):
    """The assertion that decides whether the sandbox holds.

    Metric.run_id is a foreign key to run.id, and SQLite is not enforcing it
    here -- there is no PRAGMA foreign_keys=ON anywhere. So a row written with
    a run id that matches nothing inserts happily, and pipeline_run.id and
    run.id are independent sequences that both start at 1: a pipeline metric
    would land in the metric list of the real run with that id and show up in
    its live chart.
    """
    session_factory = client.app.container["session_factory"]
    with session_factory() as db:
        assert db.query(Metric).count() == 0


def test_the_model_did_ask_to_log_and_was_stopped(finished_pipeline_run):
    """What makes the empty Metric table a consequence, not a coincidence.

    GraphModel calls calculate_metrics on every train call, the way the
    torch-based models do. So the run above genuinely tried to write metric
    rows and wrote none, and it tried with a model that had no run -- which is
    the only thing standing between it and a row keyed by nothing.
    """
    assert LOG_ATTEMPTS, "the model never tried to log, so nothing was tested"
    assert set(LOG_ATTEMPTS) == {None}


def test_the_sandbox_creates_no_run_and_no_model_session(client, finished_pipeline_run):
    """No application entity is manufactured to make a pipeline work.

    A Run needs a ModelSession, which needs a globally unique name, a dataset,
    a task, input and output columns and splits, all NOT NULL -- two entities
    per execution, visible in the Models UI as sessions nobody created, with a
    deletion lifecycle nobody owns.
    """
    session_factory = client.app.container["session_factory"]
    with session_factory() as db:
        assert db.query(Run).count() == 0
        assert db.query(ModelSession).count() == 0


def test_the_metrics_of_the_pipeline_live_in_an_artifact(finished_pipeline_run):
    """Where a pipeline's metrics go, now that they cannot go to Metric."""
    metrics = finished_pipeline_run["artifacts"][("eval", "metrics")]

    assert metrics == {
        "train": {"GraphMetric": 0.5},
        "validation": {"GraphMetric": 0.5},
        "test": {"GraphMetric": 0.5},
    }


def test_the_model_is_saved_where_no_real_run_could_collide_with_it(
    client, finished_pipeline_run
):
    """The artifact name, which is the other half of what run_id used to do."""
    model_path = finished_pipeline_run["artifacts"][("save", "model_path")]
    runs_path = str(client.app.container["config"]["RUNS_PATH"])

    assert model_path.startswith(runs_path)
    assert os.path.exists(model_path)

    directory = os.path.basename(model_path)
    # Not a bare integer, which is what every real run's directory is called.
    assert not directory.isdigit()
    assert directory == f"pipeline-{finished_pipeline_run['id']}-save"

    # And the model that landed there is the one that was trained.
    assert joblib.load(model_path)["trained_with"]["train"] > 0


def test_the_model_never_belonged_to_a_run(finished_pipeline_run):
    """The switch that turns metric persistence off, as it reaches the node.

    ModelFactory hangs run_id on the model instance, and
    BaseModel.calculate_metrics returns early for a model with no run. That is
    what makes the sandbox airtight without the pipeline having to intercept
    anything: not even a model that logs while training can write a row.
    """
    assert finished_pipeline_run["nodes"]["build"]["config"]["run_id"] is None
    assert finished_pipeline_run["nodes"]["fit"]["config"]["run_id"] is None


def test_the_run_records_units_not_canvas_shapes(finished_pipeline_run):
    nodes = finished_pipeline_run["nodes"]

    assert nodes["build"]["node_type"] == "BuildModelUnit"
    assert nodes["eval"]["node_type"] == "EvaluateModelToArtifactUnit"
    # One unit per block for now, so each node is its own block.
    for node_id, node in nodes.items():
        assert node["block_id"] == node_id


def test_every_serializable_output_is_recorded(finished_pipeline_run):
    """Artifacts are named by the unit's own PROVIDES keys."""
    artifacts = finished_pipeline_run["artifacts"]

    assert ("load", "dataset_id") in artifacts
    assert ("load", "dataset_path") in artifacts
    assert ("prep", "split_indexes") in artifacts
    assert ("prep", "task_name") in artifacts
    assert ("build", "model_parameters") in artifacts
    assert ("fit", "plot_paths") in artifacts
    assert ("eval", "metrics") in artifacts
    assert ("save", "model_path") in artifacts

    # The live objects are not: x, y, the task, the model and the factory are
    # all cache-half values, derivable again and never serialized.
    for key in ("dataset", "x", "y", "task", "model", "factory"):
        assert not any(recorded == key for _, recorded in artifacts)


def test_a_node_failing_halfway_cancels_the_rest(
    client: TestClient, dataset_1: Dataset, graph_registry
):
    """A run that died halfway must not look like one still in flight."""
    session_factory = client.app.container["session_factory"]
    steps, edges = _model_job_blocks(dataset_1.id)

    # A model that is not in the registry: build fails, and everything the
    # order puts after it never runs.
    for step in steps:
        if step["id"] == "build":
            step["units"][0]["config"]["model"] = {
                "component": "NoSuchModel",
                "params": {},
            }

    with session_factory() as db:
        pipeline = Pipeline(name="A graph that fails", steps=steps, edges=edges)
        db.add(pipeline)
        db.commit()
        pipeline_id = pipeline.id

    with pytest.raises(JobError):
        PipelineJob(pipeline_id=pipeline_id).run()

    with session_factory() as db:
        pipeline_run = db.query(PipelineRun).filter_by(pipeline_id=pipeline_id).one()
        statuses = {row.node_id: row.status for row in pipeline_run.node_runs}
        assert pipeline_run.status == PipelineRunStatus.ERROR

    assert statuses["load"] == NodeRunStatus.FINISHED
    assert statuses["prep"] == NodeRunStatus.FINISHED
    assert statuses["build"] == NodeRunStatus.ERROR
    assert statuses["fit"] == NodeRunStatus.CANCELLED
    assert statuses["eval"] == NodeRunStatus.CANCELLED
    assert statuses["save"] == NodeRunStatus.CANCELLED


def test_two_runs_of_the_same_graph_do_not_overwrite_each_others_model(
    client: TestClient, dataset_1: Dataset, graph_registry
):
    """Each execution names its own artifacts.

    Without the run id in the name, the second execution would write over the
    first one's model, silently.
    """
    session_factory = client.app.container["session_factory"]
    steps, edges = _model_job_blocks(dataset_1.id)

    with session_factory() as db:
        pipeline = Pipeline(name="A graph run twice", steps=steps, edges=edges)
        db.add(pipeline)
        db.commit()
        pipeline_id = pipeline.id

    PipelineJob(pipeline_id=pipeline_id).run()
    PipelineJob(pipeline_id=pipeline_id).run()

    with session_factory() as db:
        runs = (
            db.query(PipelineRun)
            .filter_by(pipeline_id=pipeline_id)
            .order_by(PipelineRun.id)
            .all()
        )
        paths = [
            db.query(NodeArtifact)
            .join(NodeRun)
            .filter(
                NodeRun.pipeline_run_id == pipeline_run.id,
                NodeArtifact.key == "model_path",
            )
            .one()
            .value
            for pipeline_run in runs
        ]

    assert len(paths) == 2
    assert paths[0] != paths[1]
    assert all(os.path.exists(path) for path in paths)


def test_the_graph_definition_survives_being_stored_as_json(
    client: TestClient, dataset_1: Dataset, graph_registry
):
    """The blocks are plain data, which is what a canvas can save and reload."""
    steps, edges = _model_job_blocks(dataset_1.id)

    assert json.loads(json.dumps(steps)) == steps
    assert json.loads(json.dumps(edges)) == edges
