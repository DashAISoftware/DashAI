"""The shape of a graph: nodes, edges, and the rule that bundles them."""

from dataclasses import dataclass, field
from typing import Any, Dict, Mapping, Optional, Sequence, Set, Tuple


class GraphError(Exception):
    """Raised when a graph is not executable as declared."""


@dataclass(frozen=True)
class Node:
    """One unit placed in a graph.

    A node carries the *name* of its unit rather than an instance. Unit
    instances hold state of their own — ``FitModelUnit`` memoizes its resolved
    optimizer, ``FitConverterUnit`` its converter class — so two nodes sharing
    one instance would have the second silently run with the first one's. The
    engine builds one instance per node from ``(unit, config)``, which is also
    exactly what a persisted graph can hold.

    Parameters
    ----------
    id : str
        Identifier of this node inside the graph.
    unit : str
        Class name of the unit, as the component registry knows it.
    config : Mapping[str, Any]
        The unit's own configuration, validated by its ``SCHEMA``. Constants a
        caller chooses live here — not in the context, where nothing upstream
        could ever supply them.
    block_id : Optional[str]
        The visual block this node belongs to, for an editor that groups
        several units into one shape on a canvas. Left out, it becomes ``id``:
        a node always belongs to some block, so nothing downstream — the
        tracking column least of all — has a null to handle, and a node has one
        representation rather than two.
    """

    id: str
    unit: str
    config: Mapping[str, Any] = field(default_factory=dict)
    block_id: Optional[str] = None

    def __post_init__(self) -> None:
        if self.block_id is None:
            object.__setattr__(self, "block_id", self.id)


@dataclass(frozen=True)
class Edge:
    """One key travelling from a node's output to another's input.

    The pair of names is what makes the fixed strings in ``REQUIRES`` and
    ``PROVIDES`` behave as port names: ``src_key`` is drawn from the source's
    ``PROVIDES`` and ``dst_key`` from the target's ``REQUIRES``, and the edge
    maps one onto the other. That is what lets two ``LoadDatasetUnit`` nodes,
    which both write the fixed key ``dataset``, coexist in one graph — the
    renaming lives here rather than in the unit.
    """

    src: str
    src_key: str
    dst: str
    dst_key: str


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

    def by_id(self) -> Dict[str, Node]:
        return {node.id: node for node in self.nodes}


def connect(src: Node, dst: Node) -> Tuple[Edge, ...]:
    """Wire every key two nodes agree on: ``PROVIDES`` against ``REQUIRES``.

    A canvas cannot draw one edge per key — ``FitModelUnit`` alone requires
    seven — so one drawn edge between two nodes stands for this whole set.

    The rule does not cover every wire a real graph needs, and that is by
    design rather than an omission: ``ApplyConverterUnit`` does not republish
    ``dataset_id``, because nothing derived from the object being transformed
    may cross the context boundary. A downstream node that needs both the
    converted dataset and the id therefore takes the id on an edge that skips
    the converter entirely.
    """
    from DashAI.back.dag.validate import resolve_unit_class

    provides = set(resolve_unit_class(src.unit).PROVIDES)
    requires = set(resolve_unit_class(dst.unit).REQUIRES)
    return tuple(Edge(src.id, key, dst.id, key) for key in sorted(provides & requires))


def sinks(graph: Graph) -> Set[str]:
    """Node ids nothing consumes. They are what a run exists to produce."""
    consumed = {edge.src for edge in graph.edges}
    return {node.id for node in graph.nodes} - consumed


def dump(graph: Graph) -> Tuple[list, list]:
    """Serialize a graph to the plain data a run freezes.

    Unit level, not block level: a run records the graph it actually executed,
    so replaying it never depends on re-running the expansion that produced it.
    """
    steps = [
        {
            "id": node.id,
            "block_id": node.block_id,
            "unit": node.unit,
            "config": dict(node.config),
        }
        for node in graph.nodes
    ]
    edges = [
        {
            "src": edge.src,
            "src_key": edge.src_key,
            "dst": edge.dst,
            "dst_key": edge.dst_key,
        }
        for edge in graph.edges
    ]
    return steps, edges


def load(
    steps: Sequence[Mapping[str, Any]], edges: Sequence[Mapping[str, Any]]
) -> Graph:
    """Rebuild a graph from what :func:`dump` produced.

    Raises
    ------
    GraphError
        If a step or an edge is missing a field. Rows written by the previous
        subsystem land here: their steps carry a node ``type`` and a single
        ``config``, with no unit to resolve, so they are refused with a message
        that says so rather than failing somewhere deeper.
    """
    try:
        nodes = [
            Node(
                id=step["id"],
                unit=step["unit"],
                config=step.get("config") or {},
                block_id=step.get("block_id"),
            )
            for step in steps
        ]
    except KeyError as e:
        raise GraphError(
            f"A step is missing the field {e}. Steps saved by the previous "
            "pipeline subsystem name a node type rather than a unit and cannot "
            "be run by this engine."
        ) from e

    try:
        wires = [
            Edge(edge["src"], edge["src_key"], edge["dst"], edge["dst_key"])
            for edge in edges
        ]
    except KeyError as e:
        raise GraphError(
            f"An edge is missing the field {e}. Edges saved by the previous "
            "pipeline subsystem connect nodes without naming the keys they "
            "carry, so they cannot be run by this engine."
        ) from e

    return Graph(nodes, wires)
