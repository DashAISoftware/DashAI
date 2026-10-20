"""Sequential execution of a validated graph.

The engine gives every node an ``ExecutionContext`` of its own, preloaded with
exactly the keys that node declares in ``REQUIRES``, and the renaming lives on
the edge. There is no shared context: merging the outputs of two predecessors
into one dictionary loses a key whenever both publish the same one, which is
how its predecessor lost values silently and why it grew a parallel list of raw
branch dictionaries to work around itself.

Nothing here touches the database. Tracking goes through a sink, so the engine
can run with no persistence at all — which is how it is tested.
"""

import logging
from typing import Any, Dict, List, Mapping, Optional, Protocol

from DashAI.back.dag.graph import Graph, GraphError
from DashAI.back.dag.validate import instantiate, resolve_unit_class, validate
from DashAI.back.units.context import ExecutionContext

log = logging.getLogger(__name__)


class TrackingSink(Protocol):
    """Where a run reports what it is doing.

    Every method is a notification, not a decision: a sink may persist, log, or
    do nothing, and the engine's behaviour does not depend on which.
    """

    def run_started(self, order: List[str]) -> None:
        """The graph passed validation and is about to run, in this order."""

    def node_started(self, node_id: str, payload: Mapping[str, Any]) -> None:
        """``payload`` is the serializable half of the node's input context."""

    def node_finished(
        self, node_id: str, artifacts: Mapping[str, Any], payload: Mapping[str, Any]
    ) -> None:
        """``artifacts`` are the node's serializable outputs, by PROVIDES key."""

    def node_failed(self, node_id: str, message: str) -> None: ...

    def nodes_cancelled(self, node_ids: List[str]) -> None:
        """Nodes that will never run because an earlier one failed."""

    def run_finished(self) -> None: ...

    def run_failed(self, message: str) -> None: ...


class NullSink:
    """A sink that records nothing. The engine's default."""

    def run_started(self, order: List[str]) -> None:
        pass

    def node_started(self, node_id: str, payload: Mapping[str, Any]) -> None:
        pass

    def node_finished(
        self, node_id: str, artifacts: Mapping[str, Any], payload: Mapping[str, Any]
    ) -> None:
        pass

    def node_failed(self, node_id: str, message: str) -> None:
        pass

    def nodes_cancelled(self, node_ids: List[str]) -> None:
        pass

    def run_finished(self) -> None:
        pass

    def run_failed(self, message: str) -> None:
        pass


def artifacts_of(unit_class: type, ctx: ExecutionContext) -> Dict[str, Any]:
    """The outputs of a node that can be persisted, by ``PROVIDES`` key.

    Only the reference half: the cache holds live datasets, models and tasks,
    which are not serializable and are always derivable again. A unit whose
    real output is on disk publishes the path as a reference, so the path is
    what gets recorded — which is the whole of what a caller needs later.

    ``origin`` is what makes this cheap. Asking ``key in ctx.refs`` answers the
    same question but deep-copies every reference the context holds, once per
    key.
    """
    return {
        key: ctx.get(key) for key in unit_class.PROVIDES if ctx.origin(key) == "ref"
    }


def run(
    graph: Graph, sink: Optional[TrackingSink] = None
) -> Dict[str, ExecutionContext]:
    """Execute a graph sequentially, returning the contexts still in use.

    Parameters
    ----------
    graph : Graph
        The graph to run. It is validated first, so a graph that cannot work
        fails before any unit does.
    sink : Optional[TrackingSink]
        Where progress is reported. Defaults to recording nothing.

    Returns
    -------
    Dict[str, ExecutionContext]
        The context of every node whose values were still needed at the end,
        keyed by node id. Contexts nobody reads any more are dropped as the run
        proceeds, so intermediate datasets do not pile up for the length of the
        run.

    Raises
    ------
    GraphError
        If the graph does not validate.
    """
    sink = sink if sink is not None else NullSink()

    order = validate(graph)
    by_id = graph.by_id()
    classes = {node.id: resolve_unit_class(node.unit) for node in graph.nodes}

    # One instance per node, built before anything runs: a configuration that
    # cannot build its unit is a mistake in the graph, not a failure of a node
    # halfway through it.
    units = {node.id: instantiate(node) for node in graph.nodes}

    consumers: Dict[str, int] = dict.fromkeys(by_id, 0)
    for edge in graph.edges:
        consumers[edge.src] += 1

    sink.run_started(order)

    contexts: Dict[str, ExecutionContext] = {}
    for position, node_id in enumerate(order):
        ctx = ExecutionContext()

        for edge in graph.edges:
            if edge.dst != node_id:
                continue
            source = contexts[edge.src]
            # The half a value lives in decides how it may be moved: put_ref
            # validates with json.dumps and deep-copies, put stores the live
            # object by reference. A dataset handed to put_ref raises, and a
            # reference handed to put loses its copy-on-read guarantee.
            if source.origin(edge.src_key) == "ref":
                ctx.put_ref(edge.dst_key, source.get(edge.src_key))
            else:
                ctx.put(edge.dst_key, source.require(edge.src_key))

        sink.node_started(node_id, ctx.to_dict())
        try:
            units[node_id](ctx)
        except Exception as e:
            log.exception(e)
            sink.node_failed(node_id, str(e))
            # Everything after this point in the order never runs. Reporting
            # them keeps a run that died halfway distinguishable from one still
            # in flight.
            sink.nodes_cancelled(list(order[position + 1 :]))
            sink.run_failed(str(e))
            raise

        contexts[node_id] = ctx
        sink.node_finished(node_id, artifacts_of(classes[node_id], ctx), ctx.to_dict())

        # Release what nothing downstream will read again.
        for edge in graph.edges:
            if edge.dst != node_id:
                continue
            consumers[edge.src] -= 1
            if consumers[edge.src] == 0 and edge.src in contexts:
                contexts.pop(edge.src).clear_cache()

    sink.run_finished()
    return contexts


__all__ = ["GraphError", "NullSink", "TrackingSink", "artifacts_of", "run"]
