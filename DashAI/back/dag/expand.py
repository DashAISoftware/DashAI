"""Turning what a canvas holds into the graph the engine runs.

A canvas cannot show a training as six nodes and fifteen edges, so a block on
it stands for a sequence of units. The engine works on units, so a run is over
the expanded graph, and it is the expanded graph a run freezes: replaying one
never depends on re-running the expansion that produced it.

The first version has one unit per block, and expansion is close to a rename.
The shape is here from the start because the persistence has to be right before
there is anything to migrate.
"""

import re
from typing import Any, Dict, List, Mapping, Sequence

from DashAI.back.dag.graph import Edge, Graph, GraphError, Node
from DashAI.back.dag.validate import resolve_unit_class

#: Anything outside what can name a directory under RUNS_PATH, plus the escape
#: character itself. ``SaveModelUnit.validate`` refuses the rest, so a prefix
#: built from a node id a user chose has to be brought into that alphabet here.
#:
#: ``_`` is in here on purpose. Replacing unsafe characters with a fixed ``_``
#: is not injective -- ``save.a`` and ``save_a`` would collapse to the same
#: name, and the second saving node would overwrite the first one's model
#: directory in silence. Escaping to ``_<hex>`` instead, with ``_`` itself
#: escaped, is reversible, so two different node ids cannot produce one prefix.
_NEEDS_ESCAPE = re.compile(r"[^A-Za-z0-9-]")

#: The runtime params this module knows how to answer. A unit declares which
#: ones it takes in its own ``RUNTIME_PARAMS``; these are the two that are about
#: the pipeline run rather than about a job, so a pipeline is what supplies them.
#: Any other runtime param belongs to whoever else runs that unit.
ENGINE_SUPPLIED = ("artifact_prefix", "run_id")


def artifact_prefix(pipeline_run_id: int, node_id: str) -> str:
    """Name this node's artifacts so nothing else can collide with them.

    The runs directory is shared with every real ``Run``, and a pipeline run id
    is a different sequence from a run id: both start at 1, so a pipeline that
    used its own id as the name would write over the model of the run with that
    id. Not a risk -- a certainty. The ``pipeline-`` prefix is what keeps the
    two apart, the run id keeps two executions of the same pipeline apart, and
    the node id keeps two saving nodes in one graph apart.

    The node id is escaped rather than cleaned, so the mapping is injective and
    two different ids can never produce one prefix.
    """
    escaped = _NEEDS_ESCAPE.sub(
        lambda match: f"_{ord(match.group()):02x}", str(node_id)
    )
    return f"pipeline-{pipeline_run_id}-{escaped}"


def expand(
    steps: Sequence[Mapping[str, Any]],
    edges: Sequence[Mapping[str, Any]],
    pipeline_run_id: int,
) -> Graph:
    """Expand a canvas into a unit-level graph.

    Parameters
    ----------
    steps : Sequence[Mapping[str, Any]]
        The blocks, each ``{id, units: [{id, unit, config}], ...}``.
    edges : Sequence[Mapping[str, Any]]
        The wires between blocks, each ``{source, target}``.
    pipeline_run_id : int
        The run being expanded, which is what names its artifacts.

    Returns
    -------
    Graph
        Nodes are units, and every node carries the block it came from.

    Raises
    ------
    GraphError
        If a block is malformed, or if it holds more than one unit — see the
        note below.

    Notes
    -----
    A block holding several units is refused rather than guessed at. Wiring
    across a boundary where either side is a sequence has more than one
    defensible answer, and the rule that bundles keys does not cover every wire
    a real graph needs: ``ApplyConverterUnit`` deliberately does not republish
    ``dataset_id``, so a node needing both the converted dataset and the id
    takes the id on an edge that skips the converter. Choosing a rule for that
    without a case to check it against would be inventing semantics. The
    persistence already carries N units per block, so adding it later costs no
    migration.
    """
    blocks = _read_blocks(steps)

    nodes: List[Node] = []
    for block_id, units in blocks.items():
        for unit in units:
            nodes.append(
                Node(
                    id=unit["id"],
                    unit=unit["unit"],
                    config=_with_engine_config(
                        unit["unit"],
                        unit.get("config") or {},
                        pipeline_run_id,
                        unit["id"],
                    ),
                    block_id=block_id,
                )
            )

    wires: List[Edge] = []
    for edge in edges:
        source, target = edge.get("source"), edge.get("target")
        if source not in blocks or target not in blocks:
            raise GraphError(
                f"An edge connects '{source}' to '{target}', and one of them is "
                "not a block in this pipeline."
            )
        wires.extend(_between(blocks[source][-1], blocks[target][0]))

    return Graph(nodes, wires)


def _read_blocks(
    steps: Sequence[Mapping[str, Any]],
) -> Dict[str, List[Mapping[str, Any]]]:
    """Validate the shape of the blocks and index them by id."""
    blocks: Dict[str, List[Mapping[str, Any]]] = {}

    for step in steps:
        block_id = step.get("id")
        if not block_id:
            raise GraphError("A block has no id.")
        if block_id in blocks:
            raise GraphError(f"There is more than one block with the id '{block_id}'.")

        units = step.get("units")
        if not units:
            raise GraphError(
                f"Block '{block_id}' declares no units. Blocks saved by the "
                "previous pipeline subsystem name a node type and carry a "
                "single config instead, and cannot be run by this engine."
            )
        if len(units) > 1:
            raise GraphError(
                f"Block '{block_id}' holds {len(units)} units. Only one unit "
                "per block is supported so far."
            )
        for unit in units:
            if not unit.get("id") or not unit.get("unit"):
                raise GraphError(
                    f"A unit in block '{block_id}' is missing its id or its unit name."
                )

        blocks[block_id] = list(units)

    return blocks


def _with_engine_config(
    unit_name: str,
    config: Mapping[str, Any],
    pipeline_run_id: int,
    node_id: str,
) -> Dict[str, Any]:
    """Set the configuration the engine owns rather than the user.

    Whatever the stored graph holds for these fields is **discarded**, not
    merged. Neither is a value a user could get right:

    * ``artifact_prefix`` is built from the id of the run, and there is no run
      when a node is configured -- so any value already there was chosen
      without the one thing that decides it. Overriding is also what makes two
      nodes sharing a prefix impossible rather than merely unlikely, so the
      collision needs no validator to catch it.
    * ``run_id`` is null because a pipeline has no ``Run`` row. Forcing it is
      what makes the sandbox mechanical instead of conventional: a stored graph
      cannot point a training node at a real run and start writing ``Metric``
      rows into it.

    Both are declared in the unit's ``RUNTIME_PARAMS`` rather than in its
    schema, so a form never offers them in the first place. This is the other
    half of the same statement, on the side a hand-edited row could still reach.
    """
    resolved = dict(config)
    takes = set(resolve_unit_class(unit_name).RUNTIME_PARAMS)

    if "artifact_prefix" in takes:
        resolved["artifact_prefix"] = artifact_prefix(pipeline_run_id, node_id)

    if "run_id" in takes:
        resolved["run_id"] = None

    return resolved


def _between(source: Mapping[str, Any], target: Mapping[str, Any]) -> List[Edge]:
    """Wire the keys the two units agree on: ``PROVIDES`` against ``REQUIRES``.

    One drawn edge stands for the whole set, because a canvas cannot draw one
    per key.
    """
    provides = set(resolve_unit_class(source["unit"]).PROVIDES)
    requires = set(resolve_unit_class(target["unit"]).REQUIRES)
    shared = sorted(provides & requires)

    if not shared:
        raise GraphError(
            f"'{source['id']}' ({source['unit']}) has nothing "
            f"'{target['id']}' ({target['unit']}) needs, so the edge between "
            "them would carry nothing."
        )

    return [Edge(source["id"], key, target["id"], key) for key in shared]
