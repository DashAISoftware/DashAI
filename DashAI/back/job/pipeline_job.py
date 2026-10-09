"""Job that runs a pipeline as a graph of units."""

import logging
from typing import TYPE_CHECKING

from kink import inject

from DashAI.back.dag.engine import run as run_graph
from DashAI.back.dag.expand import expand
from DashAI.back.dag.graph import GraphError
from DashAI.back.dag.tracking import DatabaseSink
from DashAI.back.job.base_job import BaseJob, JobError

if TYPE_CHECKING:
    from sqlalchemy.orm import sessionmaker

log = logging.getLogger(__name__)


class PipelineJob(BaseJob):
    """Run a pipeline: expand its blocks into units and execute the graph.

    The job owns what a job owns -- the database session, the run row, its
    status transitions -- and the engine owns execution. Between them sits the
    expansion, which needs the run's id: naming a node's artifacts has to
    happen before the graph is built, so the row is created here first and the
    engine never creates anything.

    ``kwargs`` is a single id, as every job's is: the whole job is serialized
    with dill to reach the worker process, which rebuilds its dependencies from
    a fresh container, so nothing but plain data can travel in it. The graph is
    read from the database inside ``run``.
    """

    @staticmethod
    def _pipeline_id(kwargs) -> int:
        """The id of the pipeline to run, under either name it arrives as.

        The front sends ``{"id": …}`` -- the wire contract predates this job --
        while every sibling job names its own subject (``run_id``,
        ``converter_id``). Both are accepted so the existing caller keeps
        working and a new one can use the name that matches the others; the
        fallback goes when the endpoint is rewritten.
        """
        pipeline_id = kwargs.get("pipeline_id", kwargs.get("id"))
        if pipeline_id is None:
            raise JobError("No pipeline id was given to run. Send it as 'pipeline_id'.")
        return pipeline_id

    def set_status_as_delivered(self) -> None:
        """Nothing to mark: the run row does not exist until the job starts.

        A pipeline has no per-pipeline status, and the run row is created in
        ``run`` because expanding the graph needs its id. Recording the
        delivered state would mean creating the row when the job is enqueued
        instead, which belongs with the endpoint that enqueues it.
        """
        log.debug("PipelineJob delivered; no row to mark yet.")

    def set_status_as_error(self) -> None:
        """Nothing to mark.

        This is called on a job deleted while still queued, before ``run`` has
        created anything. A run that has started and then failed is marked by
        the sink, from inside ``run``.
        """
        log.debug("PipelineJob errored before starting; no row to mark.")

    @inject
    def get_job_name(self) -> str:
        """Get a descriptive name for the job."""
        from kink import di

        from DashAI.back.dependencies.database.models import Pipeline

        try:
            pipeline_id = self._pipeline_id(self.kwargs)
        except JobError:
            return "Pipeline"

        try:
            with di["session_factory"]() as db:
                pipeline = db.get(Pipeline, pipeline_id)
                if pipeline and pipeline.name:
                    return f"Pipeline: {pipeline.name}"
        except Exception:
            pass

        return f"Pipeline ({pipeline_id})"

    @inject
    def run(
        self,
        session_factory: "sessionmaker" = lambda di: di["session_factory"],
    ) -> None:
        import gc

        from DashAI.back.dependencies.database.models import Pipeline, PipelineRun

        pipeline_id: int = self._pipeline_id(self.kwargs)

        with session_factory() as db:
            pipeline: Pipeline = db.get(Pipeline, pipeline_id)
            if not pipeline:
                raise JobError(f"Pipeline {pipeline_id} does not exist in DB.")

            steps = pipeline.steps or []
            edges = pipeline.edges or []
            if not steps:
                raise JobError(f"Pipeline {pipeline_id} has no steps to run.")

            # Created before the graph is built, because naming a node's
            # artifacts needs the run's id: two executions of one pipeline that
            # shared a name would have the second write over the first's model.
            pipeline_run = PipelineRun(pipeline_id=pipeline_id)
            db.add(pipeline_run)
            db.commit()
            pipeline_run_id = pipeline_run.id

        self.report_progress(0.05, "Preparing the graph")

        try:
            graph = expand(steps, edges, pipeline_run_id)
        except GraphError as e:
            self._fail(session_factory, pipeline_run_id, str(e))
            raise JobError(str(e)) from e

        sink = DatabaseSink(pipeline_run_id, graph)

        try:
            contexts = run_graph(graph, sink)
        except GraphError as e:
            # Validation happens before the engine reports anything, so the run
            # is still untouched and saying why is this job's to do.
            self._fail(session_factory, pipeline_run_id, str(e))
            raise JobError(str(e)) from e
        except Exception as e:
            # A node failed, and the sink normally recorded which one. But the
            # sink's own calls are outside the engine's try, so one of them
            # failing -- a locked database, a run row deleted underneath -- is
            # also how we get here, and then nothing was recorded at all. _fail
            # only writes when the run is not already in a terminal state, so
            # calling it either way cannot overwrite what the sink said.
            self._fail(session_factory, pipeline_run_id, str(e))
            raise JobError(str(e)) from e
        finally:
            gc.collect()

        # The contexts of the leaves are all that is still held. Their live
        # objects are datasets and models, which nothing will read again.
        for ctx in contexts.values():
            ctx.clear_cache()
        gc.collect()

        self.report_progress(1.0, "Finished")

    @staticmethod
    def _fail(session_factory, pipeline_run_id: int, message: str) -> None:
        """Mark the run as failed, unless something already settled it.

        Never overwrites a terminal status. The sink records a node failure
        with the message the unit produced, which is the better one; this is
        the backstop for the paths where nothing recorded anything, and a run
        left in STARTED with no error is indistinguishable from one still
        going.
        """
        from DashAI.back.core.enums.status import PipelineRunStatus
        from DashAI.back.dependencies.database.models import PipelineRun

        settled = {
            PipelineRunStatus.FINISHED,
            PipelineRunStatus.ERROR,
        }

        with session_factory() as db:
            pipeline_run = db.get(PipelineRun, pipeline_run_id)
            if pipeline_run is None or pipeline_run.status in settled:
                return
            pipeline_run.set_status_as_error(message)
            db.commit()
