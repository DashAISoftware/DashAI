"""PipelineJob end to end, against a real database.

Its predecessor implemented two of BaseJob's four abstract methods, so it could
not be instantiated at all: asking the job endpoint for a PipelineJob raised
TypeError. These check the job runs, and that the four methods are there.
"""

import pytest
from kink import di
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from DashAI.back.core.enums.status import NodeRunStatus, PipelineRunStatus
from DashAI.back.dependencies.database.models import (
    Base,
    NodeArtifact,
    NodeRun,
    Pipeline,
    PipelineRun,
)
from DashAI.back.job.base_job import BaseJob, JobError
from DashAI.back.job.pipeline_job import PipelineJob
from DashAI.back.units.base_unit import BaseUnit


class _EmitUnit(BaseUnit):
    REQUIRES = ()
    PROVIDES = ("dataset_path", "dataset")

    def execute(self, ctx):
        ctx.put_ref("dataset_path", "/tmp/ds")
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
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine)

    class _Factory:
        def __call__(self):
            return factory()

    di["session_factory"] = _Factory()
    di["component_registry"] = {
        "EmitUnit": {"class": _EmitUnit},
        "ConsumeUnit": {"class": _ConsumeUnit},
        "FailUnit": {"class": _FailUnit},
    }
    yield factory
    del di["session_factory"]
    del di["component_registry"]
    engine.dispose()


def _pipeline(factory, steps, edges, name="a pipeline"):
    with factory() as db:
        pipeline = Pipeline(name=name, steps=steps, edges=edges)
        db.add(pipeline)
        db.commit()
        return pipeline.id


def _block(block_id, unit):
    return {
        "id": block_id,
        "units": [{"id": block_id, "unit": unit, "config": {}}],
    }


def test_the_job_implements_every_abstract_method_of_base_job():
    """The reason its predecessor could not be instantiated at all."""
    missing = {
        name
        for name in getattr(BaseJob, "__abstractmethods__", set())
        if getattr(PipelineJob, name) is getattr(BaseJob, name)
    }
    assert not missing
    assert PipelineJob(pipeline_id=1) is not None


def test_a_pipeline_runs_and_records_what_each_node_produced(database):
    pipeline_id = _pipeline(
        database,
        [_block("emit-1", "EmitUnit"), _block("consume-1", "ConsumeUnit")],
        [{"source": "emit-1", "target": "consume-1"}],
    )

    PipelineJob(pipeline_id=pipeline_id).run()

    with database() as db:
        pipeline_run = db.query(PipelineRun).one()
        assert pipeline_run.status == PipelineRunStatus.FINISHED
        assert {row.node_id for row in pipeline_run.node_runs} == {
            "emit-1",
            "consume-1",
        }
        assert {row.status for row in pipeline_run.node_runs} == {
            NodeRunStatus.FINISHED
        }
        artifacts = {
            (row.node_run.node_id, row.key) for row in db.query(NodeArtifact).all()
        }

    assert artifacts == {
        ("emit-1", "dataset_path"),
        ("consume-1", "results_path"),
    }


def test_the_run_freezes_the_expanded_graph(database):
    """A run records units and keys, not the blocks a canvas drew."""
    pipeline_id = _pipeline(
        database,
        [_block("emit-1", "EmitUnit"), _block("consume-1", "ConsumeUnit")],
        [{"source": "emit-1", "target": "consume-1"}],
    )

    PipelineJob(pipeline_id=pipeline_id).run()

    with database() as db:
        pipeline_run = db.query(PipelineRun).one()

    assert pipeline_run.edges == [
        {
            "src": "emit-1",
            "src_key": "dataset",
            "dst": "consume-1",
            "dst_key": "dataset",
        }
    ]
    assert [step["unit"] for step in pipeline_run.steps] == [
        "EmitUnit",
        "ConsumeUnit",
    ]


def test_a_graph_that_cannot_work_says_why_and_marks_the_run(database):
    """An unfed input is a mistake in the graph, reported as one."""
    pipeline_id = _pipeline(database, [_block("consume-1", "ConsumeUnit")], [])

    with pytest.raises(JobError, match="requires 'dataset'"):
        PipelineJob(pipeline_id=pipeline_id).run()

    with database() as db:
        pipeline_run = db.query(PipelineRun).one()
        assert pipeline_run.status == PipelineRunStatus.ERROR
        assert "requires 'dataset'" in pipeline_run.error_message
        # Nothing ran, so there is nothing to show per node.
        assert db.query(NodeRun).count() == 0


def test_steps_from_the_previous_subsystem_are_refused_by_name(database):
    """Rows the old canvas saved name a node type and have no unit."""
    pipeline_id = _pipeline(
        database,
        [{"id": "DataSelector-1", "type": "DataSelector", "config": {}}],
        [],
    )

    with pytest.raises(JobError, match="previous pipeline subsystem"):
        PipelineJob(pipeline_id=pipeline_id).run()

    with database() as db:
        assert db.query(PipelineRun).one().status == PipelineRunStatus.ERROR


def test_a_pipeline_with_no_steps_is_refused_before_a_run_is_created(database):
    pipeline_id = _pipeline(database, [], [])

    with pytest.raises(JobError, match="no steps"):
        PipelineJob(pipeline_id=pipeline_id).run()

    with database() as db:
        assert db.query(PipelineRun).count() == 0


def test_a_missing_pipeline_is_refused(database):
    with pytest.raises(JobError, match="does not exist"):
        PipelineJob(pipeline_id=9999).run()


def test_two_runs_of_one_pipeline_name_their_artifacts_apart(database):
    """The reason the run row is created before the graph is expanded."""
    pipeline_id = _pipeline(database, [_block("emit-1", "EmitUnit")], [])

    PipelineJob(pipeline_id=pipeline_id).run()
    PipelineJob(pipeline_id=pipeline_id).run()

    with database() as db:
        runs = db.query(PipelineRun).order_by(PipelineRun.id).all()
        assert len(runs) == 2
        assert runs[0].id != runs[1].id
        # Both runs recorded their own history rather than overwriting one.
        assert {row.status for run in runs for row in run.node_runs} == {
            NodeRunStatus.FINISHED
        }


def test_the_job_name_comes_from_the_pipeline(database):
    pipeline_id = _pipeline(database, [], [], name="my flow")

    assert PipelineJob(pipeline_id=pipeline_id).get_job_name() == "Pipeline: my flow"
    assert PipelineJob(pipeline_id=9999).get_job_name() == "Pipeline (9999)"


def test_the_job_kwargs_are_only_plain_data(database):
    """The whole job is serialized with dill to reach the worker process."""
    import dill

    job = PipelineJob(pipeline_id=7)

    assert job.kwargs == {"pipeline_id": 7}
    assert dill.loads(dill.dumps(job)).kwargs == {"pipeline_id": 7}


def test_the_id_the_front_actually_sends_is_accepted(database):
    """Regression: the wire contract predates this job.

    ``api/job.ts`` posts ``kwargs: {id: pipelineId}``, and ``jobs.py`` passes
    kwargs through verbatim. Reading only ``pipeline_id`` meant every enqueued
    pipeline died in the worker with a raw KeyError, before any run row existed.
    """
    pipeline_id = _pipeline(database, [_block("emit-1", "EmitUnit")], [])

    PipelineJob(id=pipeline_id).run()

    with database() as db:
        assert db.query(PipelineRun).one().status == PipelineRunStatus.FINISHED


def test_either_name_reaches_the_same_pipeline(database):
    pipeline_id = _pipeline(database, [], [], name="named")

    assert PipelineJob(id=pipeline_id).get_job_name() == "Pipeline: named"
    assert PipelineJob(pipeline_id=pipeline_id).get_job_name() == "Pipeline: named"


def test_a_job_with_no_id_at_all_says_so(database):
    with pytest.raises(JobError, match="No pipeline id"):
        PipelineJob().run()

    assert PipelineJob().get_job_name() == "Pipeline"


def test_a_run_is_never_left_looking_like_it_is_still_going(database, monkeypatch):
    """The backstop for the paths where the sink recorded nothing.

    The sink's own calls sit outside the engine's try, so one of them failing
    -- a locked database, a run row deleted underneath -- raises without any
    status having been written. A run stuck in STARTED with no error message is
    indistinguishable from one still in flight.
    """
    from DashAI.back.dag import tracking

    def explode(self, node_id, payload):
        raise RuntimeError("the sink could not write")

    monkeypatch.setattr(tracking.DatabaseSink, "node_started", explode)

    pipeline_id = _pipeline(database, [_block("emit-1", "EmitUnit")], [])

    with pytest.raises(JobError, match="could not write"):
        PipelineJob(pipeline_id=pipeline_id).run()

    with database() as db:
        pipeline_run = db.query(PipelineRun).one()
        assert pipeline_run.status == PipelineRunStatus.ERROR
        assert "could not write" in pipeline_run.error_message


def test_the_backstop_does_not_overwrite_what_the_sink_recorded(database):
    """A node's own message is the better one, so it has to survive."""
    pipeline_id = _pipeline(
        database,
        [_block("emit-1", "EmitUnit"), _block("boom-1", "FailUnit")],
        [{"source": "emit-1", "target": "boom-1"}],
    )

    with pytest.raises(JobError, match="always going to fail"):
        PipelineJob(pipeline_id=pipeline_id).run()

    with database() as db:
        pipeline_run = db.query(PipelineRun).one()
        assert pipeline_run.status == PipelineRunStatus.ERROR
        assert "always going to fail" in pipeline_run.error_message


class _NeedsARuntimeParam(BaseUnit):
    """Stands in for a unit only a particular job knows how to configure."""

    REQUIRES = ()
    PROVIDES = ("dataset_path",)
    RUNTIME_PARAMS = ("temp_path",)

    def execute(self, ctx):
        ctx.put_ref("dataset_path", self.config["temp_path"])


def test_a_runtime_param_nobody_supplies_fails_before_anything_runs(database):
    """Not halfway through, after earlier nodes already wrote to disk.

    Only two runtime params are about a pipeline run, so the engine can answer
    those. A unit whose runtime params only a particular job knows how to fill
    is not usable as a node yet, and this is where a user is told so.
    """
    di["component_registry"]["NeedsARuntimeParam"] = {"class": _NeedsARuntimeParam}
    pipeline_id = _pipeline(database, [_block("odd-1", "NeedsARuntimeParam")], [])

    with pytest.raises(JobError, match=r"needs \['temp_path'\]"):
        PipelineJob(pipeline_id=pipeline_id).run()

    with database() as db:
        assert db.query(PipelineRun).one().status == PipelineRunStatus.ERROR
        # Nothing ran, so there is nothing to show per node.
        assert db.query(NodeRun).count() == 0
