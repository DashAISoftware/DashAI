"""What a run writes down, against a real database.

The engine is exercised with a sink that records nothing in test_engine.py;
this checks the sink that persists, including the two things "no row" cannot
express: a node still waiting its turn, and a node whose run died before
reaching it.
"""

import pytest
from kink import di
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from DashAI.back.core.enums.status import NodeRunStatus, PipelineRunStatus
from DashAI.back.dag.engine import run
from DashAI.back.dag.graph import Edge, Graph, GraphError, Node, dump, load
from DashAI.back.dag.tracking import DatabaseSink
from DashAI.back.dependencies.database.models import (
    Base,
    NodeArtifact,
    NodeRun,
    Pipeline,
    PipelineRun,
)
from DashAI.back.job.base_job import JobError
from DashAI.back.units.base_unit import BaseUnit


class _EmitUnit(BaseUnit):
    """Publishes a reference and a live object, so both halves are covered."""

    REQUIRES = ()
    PROVIDES = ("dataset_path", "dataset")

    def execute(self, ctx):
        ctx.put_ref("dataset_path", self.config["path"])
        ctx.put("dataset", object())


class _ConsumeUnit(BaseUnit):
    REQUIRES = ("dataset",)
    PROVIDES = ("results_path",)

    def execute(self, ctx):
        ctx.require("dataset")
        ctx.put_ref("results_path", "/tmp/results.json")


class _FailUnit(BaseUnit):
    REQUIRES = ("dataset",)
    PROVIDES = ()

    def execute(self, ctx):
        raise JobError("this node was always going to fail")


@pytest.fixture(name="database")
def fixture_database():
    """An in-memory database shared across sessions.

    StaticPool because every notification opens its own session: without it
    each connection would get a fresh empty database.
    """
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine)

    class _Factory:
        """Not a lambda: kink calls a registered lambda when resolving it."""

        def __call__(self):
            return factory()

    di["session_factory"] = _Factory()
    di["component_registry"] = {
        "EmitUnit": {"class": _EmitUnit},
        "ConsumeUnit": {"class": _ConsumeUnit},
        "FailUnit": {"class": _FailUnit},
    }

    with factory() as db:
        pipeline = Pipeline(name="a pipeline", steps=[], edges=[])
        db.add(pipeline)
        db.commit()
        # The run row is the caller's to create: naming a node's artifacts
        # needs its id, and that comes before the graph exists.
        pipeline_run = PipelineRun(pipeline_id=pipeline.id)
        db.add(pipeline_run)
        db.commit()
        pipeline_run_id = pipeline_run.id

    yield factory, pipeline_run_id

    del di["session_factory"]
    del di["component_registry"]
    engine.dispose()


def _pair_graph():
    emit = Node("emit", "EmitUnit", {"path": "/tmp/ds"})
    consume = Node("consume", "ConsumeUnit")
    return Graph([emit, consume], [Edge("emit", "dataset", "consume", "dataset")])


def test_a_finished_run_records_every_node_and_its_artifacts(database):
    factory, pipeline_run_id = database
    graph = _pair_graph()
    sink = DatabaseSink(pipeline_run_id, graph)

    run(graph, sink)

    with factory() as db:
        pipeline_run = db.get(PipelineRun, sink.pipeline_run_id)
        assert pipeline_run.status == PipelineRunStatus.FINISHED
        assert pipeline_run.start_time is not None
        assert pipeline_run.end_time is not None

        node_runs = {row.node_id: row for row in pipeline_run.node_runs}
        assert set(node_runs) == {"emit", "consume"}
        for row in node_runs.values():
            assert row.status == NodeRunStatus.FINISHED
            assert row.start_time is not None
            assert row.end_time is not None

        artifacts = {
            (row.node_run.node_id, row.key): row.value
            for row in db.query(NodeArtifact).all()
        }

    # The live dataset is not recorded: the cache half is not serializable and
    # is always derivable again. The path it published is.
    assert artifacts == {
        ("emit", "dataset_path"): "/tmp/ds",
        ("consume", "results_path"): "/tmp/results.json",
    }


def test_the_run_freezes_the_graph_it_executed(database):
    """A past run stays readable after the pipeline it came from is edited."""
    factory, pipeline_run_id = database
    graph = _pair_graph()
    sink = DatabaseSink(pipeline_run_id, graph)

    run(graph, sink)

    with factory() as db:
        pipeline_run = db.get(PipelineRun, sink.pipeline_run_id)
        frozen_steps, frozen_edges = pipeline_run.steps, pipeline_run.edges

    steps, edges = dump(graph)
    assert frozen_steps == steps
    assert frozen_edges == edges
    # And the frozen form is enough to rebuild the graph, without re-running
    # whatever produced it.
    assert load(frozen_steps, frozen_edges) == graph


def test_a_failure_marks_the_node_and_cancels_the_rest(database):
    """CANCELLED is what NOT_STARTED cannot say.

    Without it, a run that died before reaching a node is indistinguishable
    from one still in flight.
    """
    factory, pipeline_run_id = database
    emit = Node("emit", "EmitUnit", {"path": "/tmp/ds"})
    boom = Node("boom", "FailUnit")
    consume = Node("consume", "ConsumeUnit")
    graph = Graph(
        [emit, boom, consume],
        [
            Edge("emit", "dataset", "boom", "dataset"),
            Edge("emit", "dataset", "consume", "dataset"),
        ],
    )
    sink = DatabaseSink(pipeline_run_id, graph)

    with pytest.raises(JobError, match="always going to fail"):
        run(graph, sink)

    with factory() as db:
        pipeline_run = db.get(PipelineRun, sink.pipeline_run_id)
        assert pipeline_run.status == PipelineRunStatus.ERROR
        assert "always going to fail" in pipeline_run.error_message

        rows = {row.node_id: row for row in pipeline_run.node_runs}

    assert rows["emit"].status == NodeRunStatus.FINISHED
    assert rows["boom"].status == NodeRunStatus.ERROR
    assert "always going to fail" in rows["boom"].error_message
    assert rows["consume"].status == NodeRunStatus.CANCELLED


def test_every_node_has_a_row_before_the_first_one_runs(database):
    """Rows exist up front, so a node waiting its turn is visible as waiting."""
    factory, pipeline_run_id = database
    graph = _pair_graph()
    sink = DatabaseSink(pipeline_run_id, graph)

    sink.run_started(["emit", "consume"])

    with factory() as db:
        rows = db.query(NodeRun).all()
        assert {row.node_id for row in rows} == {"emit", "consume"}
        assert {row.status for row in rows} == {NodeRunStatus.NOT_STARTED}


def test_a_node_belongs_to_a_block_even_when_it_is_alone(database):
    """block_id is never null, so grouping later needs no migration."""
    factory, pipeline_run_id = database
    graph = Graph(
        [Node("inner", "EmitUnit", {"path": "/tmp/ds"}, block_id="train-1")], []
    )
    sink = DatabaseSink(pipeline_run_id, graph)

    run(graph, sink)

    with factory() as db:
        row = db.query(NodeRun).one()
        assert row.node_id == "inner"
        assert row.block_id == "train-1"
        assert row.node_type == "EmitUnit"


def test_a_graph_that_does_not_validate_leaves_the_run_untouched(database):
    """Validation happens before the engine reports anything.

    So the run stays exactly as its caller made it -- no node rows, no start
    time, still NOT_STARTED -- and saying why is the caller's to do. Marking it
    started and then failed would claim a run began when nothing did.
    """
    factory, pipeline_run_id = database
    orphan = Graph([Node("consume", "ConsumeUnit")], [])
    sink = DatabaseSink(pipeline_run_id, orphan)

    with pytest.raises(GraphError, match="requires 'dataset'"):
        run(orphan, sink)

    with factory() as db:
        pipeline_run = db.get(PipelineRun, pipeline_run_id)
        assert pipeline_run.status == PipelineRunStatus.NOT_STARTED
        assert pipeline_run.start_time is None
        assert db.query(NodeRun).count() == 0


def test_the_node_input_and_output_are_the_serializable_halves(database):
    """What crossed into a node and what it left behind, as plain data."""
    factory, pipeline_run_id = database
    graph = _pair_graph()
    sink = DatabaseSink(pipeline_run_id, graph)

    run(graph, sink)

    with factory() as db:
        rows = {row.node_id: row for row in db.query(NodeRun).all()}

    # `dataset` is a live object, so it appears in neither: this is what
    # replaced skipping the key by name when serializing.
    assert rows["emit"].input == {}
    assert rows["emit"].output == {"dataset_path": "/tmp/ds"}
    assert rows["consume"].input == {}
    assert rows["consume"].output == {"results_path": "/tmp/results.json"}
