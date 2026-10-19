"""Expanding what a canvas holds into the graph the engine runs."""

import pytest
from kink import di

from DashAI.back.dag.expand import artifact_prefix, expand
from DashAI.back.dag.graph import Edge, Graph, GraphError, Node
from DashAI.back.units.fit_model_unit import FitModelUnit
from DashAI.back.units.load_dataset_unit import LoadDatasetUnit
from DashAI.back.units.save_dataset_unit import SaveDatasetUnit
from DashAI.back.units.save_model_unit import SaveModelUnit


@pytest.fixture(name="registry", autouse=True)
def fixture_registry():
    di["component_registry"] = {
        "LoadDatasetUnit": {"class": LoadDatasetUnit},
        "SaveDatasetUnit": {"class": SaveDatasetUnit},
        "SaveModelUnit": {"class": SaveModelUnit},
    }
    yield
    del di["component_registry"]


def _block(block_id, unit, config=None, unit_id=None):
    return {
        "id": block_id,
        "type": f"{unit}Block",
        "units": [{"id": unit_id or block_id, "unit": unit, "config": config or {}}],
    }


def test_one_unit_per_block_expands_to_the_graph_written_by_hand():
    steps = [
        _block("load-1", "LoadDatasetUnit", {"dataset_id": 7}),
        _block("save-1", "SaveDatasetUnit"),
    ]
    edges = [{"source": "load-1", "target": "save-1"}]

    graph = expand(steps, edges, pipeline_run_id=3)

    assert graph == Graph(
        [
            Node("load-1", "LoadDatasetUnit", {"dataset_id": 7}, block_id="load-1"),
            Node("save-1", "SaveDatasetUnit", {}, block_id="save-1"),
        ],
        [
            Edge("load-1", "dataset", "save-1", "dataset"),
            Edge("load-1", "dataset_path", "save-1", "dataset_path"),
        ],
    )


def test_one_drawn_edge_carries_every_key_the_two_units_agree_on():
    """A canvas cannot draw one edge per key, so one stands for the set."""
    steps = [
        _block("load-1", "LoadDatasetUnit", {"dataset_id": 7}),
        _block("save-1", "SaveDatasetUnit"),
    ]

    graph = expand(steps, [{"source": "load-1", "target": "save-1"}], 3)

    assert {(edge.src_key, edge.dst_key) for edge in graph.edges} == {
        ("dataset", "dataset"),
        ("dataset_path", "dataset_path"),
    }


def test_a_node_keeps_the_block_it_came_from():
    """The canvas colours a block from the status of its nodes."""
    steps = [_block("train-1", "SaveModelUnit", unit_id="train-1/save")]

    graph = expand(steps, [], pipeline_run_id=3)

    assert graph.nodes[0].id == "train-1/save"
    assert graph.nodes[0].block_id == "train-1"


def test_the_engine_names_the_artifacts_of_a_unit_that_takes_a_prefix():
    steps = [_block("save-1", "SaveModelUnit")]

    graph = expand(steps, [], pipeline_run_id=3)

    assert graph.nodes[0].config["artifact_prefix"] == "pipeline-3-save-1"


def test_a_prefix_stored_in_the_graph_is_discarded():
    """No stored value can be right, so none is honoured.

    The prefix is built from the id of the run, and there is no run when a node
    is configured -- so anything already there was chosen without the one thing
    that decides it. Overriding is also what makes two nodes sharing a prefix
    impossible rather than merely unlikely.
    """
    steps = [_block("save-1", "SaveModelUnit", {"artifact_prefix": "mine"})]

    graph = expand(steps, [], pipeline_run_id=3)

    assert graph.nodes[0].config["artifact_prefix"] == "pipeline-3-save-1"


def test_two_saving_nodes_cannot_end_up_with_the_same_prefix():
    """Which is why the collision needs no validator to catch it."""
    steps = [
        _block("save-a", "SaveModelUnit", {"artifact_prefix": "same"}),
        _block("save-b", "SaveModelUnit", {"artifact_prefix": "same"}),
    ]

    prefixes = {node.config["artifact_prefix"] for node in expand(steps, [], 3).nodes}

    assert len(prefixes) == 2


@pytest.mark.parametrize(
    ("first", "second"),
    [("save.a", "save_a"), ("train-1/build", "train-1_build"), ("a b", "a_b")],
)
def test_sanitizing_two_different_ids_cannot_produce_one_prefix(first, second):
    """The escape has to be reversible, not merely safe.

    Replacing every unsafe character with a plain ``_`` is safe but collapses
    distinct ids: ``save.a`` and ``save_a`` would land on the same directory and
    the second saving node would overwrite the first one's model in silence.
    That is why ``_`` is escaped along with everything else.
    """
    assert artifact_prefix(3, first) != artifact_prefix(3, second)


def test_a_unit_that_takes_no_prefix_does_not_get_one():
    steps = [_block("load-1", "LoadDatasetUnit", {"dataset_id": 7})]

    graph = expand(steps, [], pipeline_run_id=3)

    assert "artifact_prefix" not in graph.nodes[0].config


def test_two_runs_of_one_pipeline_name_their_artifacts_apart():
    """Otherwise the second run would write over the first one's model."""
    steps = [_block("save-1", "SaveModelUnit")]

    first = expand(steps, [], pipeline_run_id=3).nodes[0].config["artifact_prefix"]
    second = expand(steps, [], pipeline_run_id=4).nodes[0].config["artifact_prefix"]

    assert first != second


def test_the_prefix_can_never_be_read_as_a_path():
    """A node id a user chose has to be brought into the safe alphabet.

    ``os.path.join`` with a separator in the prefix produces a destination
    outside the runs directory, and ``SaveModelUnit.validate`` refuses one --
    so an id with a slash in it has to be sanitized here rather than failing at
    the node.
    """
    # Each unsafe character becomes _<hex>, so the mapping is reversible.
    assert artifact_prefix(3, "train-1/save") == "pipeline-3-train-1_2fsave"
    # The dot is escaped too, which is what leaves a parent reference inert
    # rather than merely separator-free.
    assert artifact_prefix(3, "../escape") == "pipeline-3-_2e_2e_2fescape"

    steps = [_block("save-1", "SaveModelUnit", unit_id="train-1/save")]
    prefix = expand(steps, [], 3).nodes[0].config["artifact_prefix"]

    # And what comes out passes the guard at the unit.
    SaveModelUnit(artifact_prefix=prefix).validate(None)


def test_a_pipeline_run_id_alone_would_collide_with_a_real_run():
    """The whole reason the prefix is not just the id.

    RUNS_PATH is shared with every real Run, and pipeline_run.id and run.id are
    independent sequences that both start at 1.
    """
    assert artifact_prefix(3, "save-1") != "3"
    assert artifact_prefix(3, "save-1").startswith("pipeline-")


def test_a_block_with_no_units_is_refused_by_name():
    """Rows written by the previous subsystem land here.

    Their steps name a node type and carry a single config, with no unit to
    resolve, so they are refused with a message that says so rather than
    failing somewhere deeper.
    """
    old_style = [{"id": "DataSelector-1", "type": "DataSelector", "config": {}}]

    with pytest.raises(GraphError, match="previous pipeline subsystem"):
        expand(old_style, [], 3)


def test_more_than_one_unit_per_block_is_refused_rather_than_guessed():
    """Wiring across a sequence boundary has more than one defensible answer."""
    steps = [
        {
            "id": "train-1",
            "units": [
                {"id": "a", "unit": "LoadDatasetUnit", "config": {"dataset_id": 7}},
                {"id": "b", "unit": "SaveDatasetUnit", "config": {}},
            ],
        }
    ]

    with pytest.raises(GraphError, match="one unit per block"):
        expand(steps, [], 3)


def test_a_block_without_an_id_is_refused():
    with pytest.raises(GraphError, match="no id"):
        expand([{"units": []}], [], 3)


def test_two_blocks_with_the_same_id_are_refused():
    steps = [
        _block("same", "LoadDatasetUnit", {"dataset_id": 7}),
        _block("same", "SaveDatasetUnit"),
    ]

    with pytest.raises(GraphError, match="more than one block"):
        expand(steps, [], 3)


def test_an_edge_to_a_block_that_is_not_there_is_refused():
    steps = [_block("load-1", "LoadDatasetUnit", {"dataset_id": 7})]

    with pytest.raises(GraphError, match="not a block"):
        expand(steps, [{"source": "load-1", "target": "ghost"}], 3)


def test_an_edge_that_would_carry_nothing_is_refused():
    """Two units with no key in common cannot be usefully connected."""
    steps = [
        _block("save-1", "SaveModelUnit"),
        _block("load-1", "LoadDatasetUnit", {"dataset_id": 7}),
    ]

    with pytest.raises(GraphError, match="would carry nothing"):
        expand(steps, [{"source": "save-1", "target": "load-1"}], 3)


def test_a_node_that_takes_a_run_id_is_told_there_is_no_run():
    """A pipeline has no Run row, and that is a value rather than an omission.

    It is how a node says the model it builds belongs to no run, which is what
    keeps that model from trying to log metrics against a foreign key that
    points at nothing.
    """
    di["component_registry"]["FitModelUnit"] = {"class": FitModelUnit}
    steps = [
        _block(
            "fit-1",
            "FitModelUnit",
            {
                "optimizer": {"component": "OptunaOptimizer", "params": {}},
                "goal_metric": "Accuracy",
            },
        )
    ]

    config = expand(steps, [], pipeline_run_id=3).nodes[0].config

    assert config["run_id"] is None
    assert config["artifact_prefix"] == "pipeline-3-fit-1"


def test_a_run_id_stored_in_the_graph_is_discarded():
    """A pipeline has no run, so a stored one is overridden rather than trusted.

    This is what makes the sandbox mechanical instead of conventional: a
    hand-edited row cannot point a training node at a real run and start
    writing Metric rows into it.
    """
    di["component_registry"]["FitModelUnit"] = {"class": FitModelUnit}
    steps = [
        _block(
            "fit-1",
            "FitModelUnit",
            {
                "optimizer": {"component": "OptunaOptimizer", "params": {}},
                "goal_metric": "Accuracy",
                "run_id": 17,
            },
        )
    ]

    assert expand(steps, [], 3).nodes[0].config["run_id"] is None
