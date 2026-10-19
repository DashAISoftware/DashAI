"""Static validation of a graph, and the registry lookup it rests on.

Everything here runs before any unit does. ``REQUIRES`` and ``PROVIDES`` are
class attributes, so the whole check needs the unit *classes* and never an
instance: a graph that cannot work is rejected without a dataset being read or
a model being built.
"""

from typing import Dict, List, Mapping

from DashAI.back.dag.graph import Edge, Graph, GraphError, Node


def resolve_unit_class(name: str) -> type:
    """Look a unit class up in the component registry by name.

    Parameters
    ----------
    name : str
        Class name of the unit.

    Returns
    -------
    type
        The unit class. Not an instance: this is what static validation reads
        ``REQUIRES`` and ``PROVIDES`` off, and building an instance would mean
        running the unit's own configuration checks too early.

    Raises
    ------
    GraphError
        If the name is unknown, or names something that is not a unit.
    """
    from kink import di

    from DashAI.back.units.base_unit import BaseUnit

    component_registry = di["component_registry"]

    try:
        unit_class = component_registry[name]["class"]
    except Exception as e:
        raise GraphError(f"There is no unit named '{name}'.") from e

    if not (isinstance(unit_class, type) and issubclass(unit_class, BaseUnit)):
        raise GraphError(
            f"'{name}' is registered but it is not a unit, so it cannot be a "
            "node in a pipeline."
        )

    return unit_class


def instantiate(node: Node):
    """Build this node's own unit instance.

    One instance per node, never shared: a unit keeps state on itself — a
    memoized optimizer, a resolved converter class — so two nodes sharing an
    instance would have the second silently run with the first one's.

    Raises
    ------
    GraphError
        If the configuration does not build the unit.
    """
    unit_class = resolve_unit_class(node.unit)
    try:
        return unit_class(**dict(node.config))
    except Exception as e:
        raise GraphError(
            f"Node '{node.id}' could not be configured as a {node.unit}: {e}"
        ) from e


def validate(graph: Graph) -> List[str]:
    """Check the graph and return a topological execution order.

    Every problem found is reported at once rather than one per run, because a
    user fixing a graph on a canvas wants the whole list.

    Two kinds of missing input are caught here: a context key no edge feeds,
    and a runtime param nobody supplied.

    There is no escape hatch for an unfed input. Every key in ``REQUIRES`` has
    a unit somewhere that publishes it — the audit in
    ``tests/back/units/test_unit_contracts.py`` enforces that — so "nothing
    supplies this key" means a missing edge and nothing else. That was not true
    while ``run_id`` was a context key no unit published: an injected constant
    and a wire the user forgot to draw were indistinguishable.

    Raises
    ------
    GraphError
        If any check fails, listing every problem found.
    """
    problems: List[str] = []

    ids = [node.id for node in graph.nodes]
    duplicates = sorted({node_id for node_id in ids if ids.count(node_id) > 1})
    if duplicates:
        problems.append(f"Duplicate node ids in the graph: {duplicates}.")

    by_id = graph.by_id()

    # Resolve every unit up front: a name that is not a unit makes every
    # contract check below meaningless, so it is reported on its own.
    classes: Dict[str, type] = {}
    for node in graph.nodes:
        try:
            classes[node.id] = resolve_unit_class(node.unit)
        except GraphError as e:
            problems.append(f"Node '{node.id}': {e}")

    if problems and not classes:
        raise GraphError("\n".join(problems))

    inbound: Dict[str, Dict[str, List[Edge]]] = {node_id: {} for node_id in by_id}

    for edge in graph.edges:
        if edge.src not in by_id or edge.dst not in by_id:
            problems.append(f"Edge {edge} points at a node that is not in the graph.")
            continue
        if edge.src in classes and edge.src_key not in classes[edge.src].PROVIDES:
            problems.append(
                f"'{edge.src}' does not provide '{edge.src_key}' "
                f"(provides: {list(classes[edge.src].PROVIDES)})."
            )
        if edge.dst in classes and edge.dst_key not in classes[edge.dst].REQUIRES:
            problems.append(
                f"'{edge.dst}' does not require '{edge.dst_key}' "
                f"(requires: {list(classes[edge.dst].REQUIRES)})."
            )
        inbound[edge.dst].setdefault(edge.dst_key, []).append(edge)

    for node in graph.nodes:
        if node.id not in classes:
            continue
        # A runtime param nobody supplied is a KeyError halfway through the
        # run otherwise -- after earlier nodes already wrote to disk. It also
        # tells a user something they need to know: a unit whose runtime params
        # only a particular job knows how to fill is not usable as a node yet.
        missing = [
            param
            for param in classes[node.id].RUNTIME_PARAMS
            if param not in node.config
        ]
        if missing:
            problems.append(
                f"'{node.id}' ({node.unit}) needs {missing} supplied by "
                "whatever runs it, and nothing in this pipeline supplies them."
            )
        for key in classes[node.id].REQUIRES:
            sources = len(inbound[node.id].get(key, []))
            if sources == 0:
                problems.append(
                    f"'{node.id}' requires '{key}' and no edge supplies it."
                )
            elif sources > 1:
                problems.append(
                    f"'{node.id}' gets '{key}' from {sources} edges; a port "
                    "takes one. Merging two values into one input is the "
                    "ambiguity this rejects rather than resolving silently."
                )

    order = _topological_order(graph, by_id, problems)

    if problems:
        raise GraphError("\n".join(problems))

    return order


def _topological_order(
    graph: Graph, by_id: Mapping[str, Node], problems: List[str]
) -> List[str]:
    """Kahn's algorithm. Nodes left over are a cycle, found before running."""
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
