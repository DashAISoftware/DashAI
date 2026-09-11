"""Persistence of a run: the sink the engine reports to.

Kept apart from the engine on purpose. The engine decides what happens and in
what order; this decides what is written down about it, and the engine runs
identically with a sink that writes nothing.

The run row is created by the caller, not here. Naming a run's artifacts needs
its id, and that has to happen before the graph is built rather than after, so
the caller creates the row, expands with its id, and hands the id over. This
writes progress into it and nothing else -- a graph that fails to validate
leaves the row exactly as the caller made it, and saying why is the caller's
job.
"""

import logging
from typing import Any, Dict, List, Mapping

from DashAI.back.dag.graph import Graph, dump

log = logging.getLogger(__name__)


class DatabaseSink:
    """Writes a run to ``PipelineRun``, ``NodeRun`` and ``NodeArtifact``.

    Each notification opens its own short session and commits, so the canvas
    can colour a node the moment it changes rather than at the end of the run.
    That is safe here and was not in the concurrent predecessor, which needed a
    process-wide lock and retries with backoff to survive SQLite answering
    "database is locked".

    Parameters
    ----------
    pipeline_run_id : int
        The run to write into. Already created by the caller.
    graph : Graph
        The expanded, unit-level graph. It is frozen into the run, so the run
        stays readable after the pipeline it came from is edited.
    """

    def __init__(self, pipeline_run_id: int, graph: Graph) -> None:
        self.pipeline_run_id = pipeline_run_id
        self._graph = graph
        self._nodes = graph.by_id()
        #: node id -> NodeRun id, so later notifications need no lookup by name.
        self._node_run_ids: Dict[str, int] = {}

    @property
    def _session_factory(self):
        from kink import di

        return di["session_factory"]

    def run_started(self, order: List[str]) -> None:
        """Freeze the graph into the run, and create a row per node.

        Every node gets a row up front, in ``NOT_STARTED``. Creating them on
        demand instead would leave a node that never ran with no row at all,
        and "no row" cannot distinguish a node still waiting from one whose run
        died before reaching it.
        """
        from DashAI.back.dependencies.database.models import NodeRun, PipelineRun

        steps, edges = dump(self._graph)

        with self._session_factory() as db:
            pipeline_run = db.get(PipelineRun, self.pipeline_run_id)
            pipeline_run.steps = steps
            pipeline_run.edges = edges
            pipeline_run.set_status_as_started()
            db.commit()

            node_runs = [
                NodeRun(
                    pipeline_run_id=self.pipeline_run_id,
                    node_id=node_id,
                    block_id=self._nodes[node_id].block_id,
                    node_type=self._nodes[node_id].unit,
                    config=dict(self._nodes[node_id].config),
                )
                for node_id in order
            ]
            db.add_all(node_runs)
            db.commit()
            self._node_run_ids = {row.node_id: row.id for row in node_runs}

    def node_started(self, node_id: str, payload: Mapping[str, Any]) -> None:
        from DashAI.back.dependencies.database.models import NodeRun

        with self._session_factory() as db:
            node_run = db.get(NodeRun, self._node_run_ids[node_id])
            node_run.set_status_as_started()
            node_run.input = dict(payload)
            db.commit()

    def node_finished(
        self, node_id: str, artifacts: Mapping[str, Any], payload: Mapping[str, Any]
    ) -> None:
        """Record the node as finished, with one artifact row per output key.

        The key is a key from the unit's own ``PROVIDES``. That is what
        replaced a column per node type: adding a kind of node used to mean
        adding a column to the pipeline table and a branch to an ``if
        node_type`` chain.
        """
        from DashAI.back.dependencies.database.models import NodeArtifact, NodeRun

        node_run_id = self._node_run_ids[node_id]
        with self._session_factory() as db:
            node_run = db.get(NodeRun, node_run_id)
            node_run.set_status_as_finished()
            node_run.output = dict(payload)
            db.add_all(
                [
                    NodeArtifact(node_run_id=node_run_id, key=key, value=value)
                    for key, value in artifacts.items()
                ]
            )
            db.commit()

    def node_failed(self, node_id: str, message: str) -> None:
        from DashAI.back.dependencies.database.models import NodeRun

        with self._session_factory() as db:
            node_run = db.get(NodeRun, self._node_run_ids[node_id])
            node_run.set_status_as_error(message)
            db.commit()

    def nodes_cancelled(self, node_ids: List[str]) -> None:
        from DashAI.back.dependencies.database.models import NodeRun

        if not node_ids:
            return

        with self._session_factory() as db:
            for node_id in node_ids:
                node_run = db.get(NodeRun, self._node_run_ids[node_id])
                node_run.set_status_as_cancelled()
            db.commit()

    def run_finished(self) -> None:
        from DashAI.back.dependencies.database.models import PipelineRun

        with self._session_factory() as db:
            pipeline_run = db.get(PipelineRun, self.pipeline_run_id)
            pipeline_run.set_status_as_finished()
            db.commit()

    def run_failed(self, message: str) -> None:
        from DashAI.back.dependencies.database.models import PipelineRun

        with self._session_factory() as db:
            pipeline_run = db.get(PipelineRun, self.pipeline_run_id)
            pipeline_run.set_status_as_error(message)
            db.commit()
