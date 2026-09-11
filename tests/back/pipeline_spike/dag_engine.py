"""Minimal sequential DAG engine over the existing atomic units.

A spike, not a deliverable. It exists to find out which parts of the unit
contract (``BaseUnit`` + ``ExecutionContext``) survive being driven by a graph
instead of by a job, before more jobs get atomized. It deliberately has no UI,
no database, no persistence, no API and no parallelism.

The one design decision it puts to the test is the one proposed in section 9 of
ATOMIZING_JOBS.md: a graph engine does not need a shared context. It gives every
node an ``ExecutionContext`` of its own, preloaded with exactly the keys that
node declares in ``REQUIRES``, and the renaming lives on the edge rather than in
the unit. That is what lets two ``LoadDatasetUnit`` instances -- both of which
write the fixed key ``dataset`` -- coexist in one graph.

Nothing here imports from ``DashAI/back/pipeline/``: that subsystem does not run
and is being redesigned. Nothing here modifies a unit either. Whatever the
engine cannot express with the contract as it stands is reported, not patched.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Mapping, Sequence, Set, Tuple

from DashAI.back.units.base_unit import BaseUnit
from DashAI.back.units.context import ExecutionContext


class GraphError(Exception):
    """Raised when a graph is not executable as declared."""


@dataclass(frozen=True)
class Node:
    """A unit instance placed in a graph.

    Parameters
    ----------
    id : str
        Identifier of the node inside the graph.
    unit : BaseUnit
        The unit instance to run. Already configured.
    seeds : Mapping[str, Any]
        Constants injected straight into this node's context, for keys no
        upstream unit publishes. ``run_id`` is the real case: four units
        require it and none provides it, because in a job it arrived through
        ``self.kwargs``. See the open question in the spike's report.
    """

    id: str
    unit: BaseUnit
    seeds: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Edge:
    """A single key travelling from one node's output to another's input.

    The pair of key names is what makes fixed ``REQUIRES``/``PROVIDES`` strings
    behave as port names: ``src_key`` is drawn from the source's ``PROVIDES``
    and ``dst_key`` from the target's ``REQUIRES``, and the edge maps one onto
    the other.
    """

    src: str
    src_key: str
    dst: str
    dst_key: str


def connect(src: Node, dst: Node) -> Tuple[Edge, ...]:
    """Wire every key the two nodes agree on: ``PROVIDES`` against ``REQUIRES``.

    A visual canvas cannot draw one edge per key: ``FitModelUnit`` alone
    requires eight. This is the bundling rule a real engine would use -- one
    drawn edge between two nodes stands for this whole set.
    """
    shared = sorted(set(src.unit.PROVIDES) & set(dst.unit.REQUIRES))
    return tuple(Edge(src.id, key, dst.id, key) for key in shared)


@dataclass(frozen=True)
class Graph:
    """A set of nodes and the edges between them."""

    nodes: Sequence[Node]
    edges: Sequence[Edge]

    def node(self, node_id: str) -> Node:
        for node in self.nodes:
            if node.id == node_id:
                return node
        raise GraphError(f"Unknown node id: {node_id}")


def validate(graph: Graph) -> List[str]:
    """Check the graph statically and return a topological execution order.

    This is the static DAG validator ATOMIZING_JOBS.md lists as missing. It is
    almost free: ``REQUIRES``/``PROVIDES`` already carry everything it needs,
    and no unit has to run.

    Raises
    ------
    GraphError
        If any check fails, with every problem found listed at once.
    """
    problems: List[str] = []
    ids = [node.id for node in graph.nodes]
    if len(set(ids)) != len(ids):
        problems.append("Duplicate node ids in the graph.")

    by_id = {node.id: node for node in graph.nodes}
    inbound: Dict[str, Dict[str, List[Edge]]] = {node_id: {} for node_id in by_id}

    for edge in graph.edges:
        if edge.src not in by_id or edge.dst not in by_id:
            problems.append(f"Edge {edge} points at a node that is not in the graph.")
            continue
        if edge.src_key not in by_id[edge.src].unit.PROVIDES:
            problems.append(
                f"{edge.src} does not provide '{edge.src_key}' "
                f"(provides: {list(by_id[edge.src].unit.PROVIDES)})."
            )
        if edge.dst_key not in by_id[edge.dst].unit.REQUIRES:
            problems.append(
                f"{edge.dst} does not require '{edge.dst_key}' "
                f"(requires: {list(by_id[edge.dst].unit.REQUIRES)})."
            )
        inbound[edge.dst].setdefault(edge.dst_key, []).append(edge)

    for node in graph.nodes:
        for key in node.seeds:
            if key not in node.unit.REQUIRES:
                problems.append(
                    f"{node.id} is seeded with '{key}', which it never uses."
                )
        for key in node.unit.REQUIRES:
            sources = len(inbound[node.id].get(key, [])) + (key in node.seeds)
            if sources == 0:
                problems.append(f"{node.id} requires '{key}' and nothing supplies it.")
            elif sources > 1:
                problems.append(
                    f"{node.id} gets '{key}' from {sources} sources; a port takes one."
                )

    order = _topological_order(graph, by_id, problems)
    if problems:
        raise GraphError("\n".join(problems))
    return order


def _topological_order(
    graph: Graph, by_id: Mapping[str, Node], problems: List[str]
) -> List[str]:
    """Kahn's algorithm. Leftover nodes mean a cycle."""
    pending = dict.fromkeys(by_id, 0)
    successors: Dict[str, List[str]] = {node_id: [] for node_id in by_id}
    for edge in graph.edges:
        if edge.src in by_id and edge.dst in by_id:
            pending[edge.dst] += 1
            successors[edge.src].append(edge.dst)

    ready = [node_id for node_id, count in pending.items() if count == 0]
    order: List[str] = []
    while ready:
        node_id = ready.pop(0)
        order.append(node_id)
        for successor in successors[node_id]:
            pending[successor] -= 1
            if pending[successor] == 0:
                ready.append(successor)

    if len(order) != len(by_id):
        problems.append(
            "The graph has a cycle: " + ", ".join(sorted(set(by_id) - set(order)))
        )
    return order


#: How many times the engine had to deep-copy the whole reference half of a
#: context just to ask which half a single key lives in. See the report.
REF_PROBES = [0]


def _transport(src_ctx: ExecutionContext, key: str) -> Tuple[str, Any]:
    """Read a value out of a context, keeping the half it came from.

    The engine has to move a value from one context to another, and the two
    halves have incompatible rules: ``put_ref`` validates with ``json.dumps``
    and deep-copies, ``put`` stores the live object by reference. Handing a
    ``DashAIDataset`` to ``put_ref`` raises; handing a dict meant as a reference
    to ``put`` silently drops the copy-on-write guarantee.

    ``ExecutionContext`` has no public way to ask which half a key is in:
    ``get``/``has`` merge them and ``refs``/``to_dict`` deep-copy the entire
    reference half. So this probe is correct but expensive, and the cost is
    counted rather than hidden.
    """
    REF_PROBES[0] += 1
    if key in src_ctx.refs:
        return "ref", src_ctx.get(key)
    return "cache", src_ctx.require(key)


def run(graph: Graph) -> Dict[str, ExecutionContext]:
    """Execute the graph sequentially and return each node's own context.

    Parameters
    ----------
    graph : Graph
        A graph that passes :func:`validate`.

    Returns
    -------
    Dict[str, ExecutionContext]
        The context of every node whose values were still needed at the end,
        keyed by node id. Contexts nobody reads any more are dropped as the run
        proceeds so intermediate datasets do not pile up.
    """
    order = validate(graph)
    by_id = {node.id: node for node in graph.nodes}

    consumers: Dict[str, int] = dict.fromkeys(by_id, 0)
    for edge in graph.edges:
        consumers[edge.src] += 1

    contexts: Dict[str, ExecutionContext] = {}
    for node_id in order:
        node = by_id[node_id]
        ctx = ExecutionContext()

        for key, value in node.seeds.items():
            ctx.put_ref(key, value)

        for edge in graph.edges:
            if edge.dst != node_id:
                continue
            half, value = _transport(contexts[edge.src], edge.src_key)
            if half == "ref":
                ctx.put_ref(edge.dst_key, value)
            else:
                ctx.put(edge.dst_key, value)

        node.unit(ctx)
        contexts[node_id] = ctx

        for edge in graph.edges:
            if edge.dst != node_id:
                continue
            consumers[edge.src] -= 1
            if consumers[edge.src] == 0:
                contexts.pop(edge.src).clear_cache()

    return contexts


def sinks(graph: Graph) -> Set[str]:
    """Node ids nothing consumes. They are what a run exists to produce."""
    consumed = {edge.src for edge in graph.edges}
    return {node.id for node in graph.nodes} - consumed
