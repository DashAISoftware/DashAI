"""The real engine, running real units as a graph, with no database.

The graph below is the train/test converter flow, which is the smallest thing a
single shared context genuinely cannot run: two ``LoadDatasetUnit`` nodes both
write the fixed key ``dataset``, so in one context the second load erases the
first.

    load_train --dataset--+-------------------> tx_train --dataset--> save_train
                          |                        ^                    ^
                          +-> fit --converter--+---+       dataset_path  |
                                               |                         --+
    load_test --dataset------------------------|-> tx_test --dataset--> save_test

Two fan-outs and two joins. The number that proves it worked is 2.0:
MinMaxScaler fitted on train [0, 5, 10] learns min=0 max=10, so a test value of
20 scales to 2.0. A refit on the test data would have produced 0.0.

The spike that established this runs the same graph against a throwaway engine
and stays as a frozen record of the unit contract. This exercises the shipped
one, which differs in the two ways that matter: nodes name their unit instead
of carrying an instance, and there are no seeds.
"""

from pathlib import Path

import pandas as pd
import pyarrow as pa
import pytest
from kink import di

from DashAI.back.converters.scikit_learn.min_max_scaler import MinMaxScaler
from DashAI.back.dag.engine import NullSink, artifacts_of, run
from DashAI.back.dag.graph import Edge, Graph, GraphError, Node, connect, sinks
from DashAI.back.dag.validate import instantiate, resolve_unit_class, validate
from DashAI.back.dataloaders.classes.dashai_dataset import (
    load_dataset,
    save_dataset,
    to_dashai_dataset,
)
from DashAI.back.job.base_job import JobError
from DashAI.back.types.value_types import Float
from DashAI.back.units.context import ExecutionContext
from DashAI.back.units.fit_converter_unit import FitConverterUnit
from DashAI.back.units.load_dataset_unit import LoadDatasetUnit
from DashAI.back.units.save_dataset_to_path_unit import SaveDatasetToPathUnit
from DashAI.back.units.save_dataset_unit import SaveDatasetUnit
from DashAI.back.units.save_model_unit import SaveModelUnit
from DashAI.back.units.transform_dataset_unit import TransformDatasetUnit

FULL_SCOPE = {"columns": [], "rows": []}


class _Row:
    """Stand-in for a Dataset ORM row, as in tests/back/units."""

    def __init__(self, file_path):
        self.file_path = file_path
        self.dataset_id = None


class _FakeSession:
    def __init__(self, rows):
        self._rows = rows

    def get(self, model, row_id):
        return self._rows.get(model.__name__, {}).get(row_id)

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        return False


class _FakeSessionFactory:
    """A class, not a lambda: kink resolves a registered lambda by calling it."""

    def __init__(self, rows):
        self._rows = rows

    def __call__(self):
        return _FakeSession(self._rows)


def _write(root, **columns):
    frame = pd.DataFrame(columns)
    types = {name: Float(arrow_type=pa.float64()) for name in frame.columns}
    save_dataset(to_dashai_dataset(frame, types=types), str(root / "dataset"))
    return root


def _values(path, column="a"):
    return list(load_dataset(str(path)).to_pandas()[column])


@pytest.fixture(name="stored_datasets")
def fixture_stored_datasets(tmp_path):
    """Dataset 7 is the training data, dataset 8 the test data.

    The engine resolves a node's unit by name, so the registry has to hold the
    unit classes as well as the converter.
    """
    train = _write(tmp_path / "train", a=[0.0, 5.0, 10.0])
    test = _write(tmp_path / "test", a=[20.0])

    di["session_factory"] = _FakeSessionFactory(
        {"Dataset": {7: _Row(str(train)), 8: _Row(str(test))}}
    )
    di["component_registry"] = {
        "MinMaxScaler": {"class": MinMaxScaler},
        "LoadDatasetUnit": {"class": LoadDatasetUnit},
        "FitConverterUnit": {"class": FitConverterUnit},
        "TransformDatasetUnit": {"class": TransformDatasetUnit},
        "SaveDatasetUnit": {"class": SaveDatasetUnit},
        "SaveDatasetToPathUnit": {"class": SaveDatasetToPathUnit},
        "SaveModelUnit": {"class": SaveModelUnit},
        "NotAUnit": {"class": MinMaxScaler},
    }
    yield train, test
    del di["session_factory"]
    del di["component_registry"]


def _graph(tmp_path, converter="MinMaxScaler"):
    """The diamond, wired with the bundling rule wherever it applies."""
    load_train = Node("load_train", "LoadDatasetUnit", {"dataset_id": 7})
    load_test = Node("load_test", "LoadDatasetUnit", {"dataset_id": 8})
    fit = Node(
        "fit",
        "FitConverterUnit",
        {
            "converter": {"component": converter, "params": {}},
            "scope": FULL_SCOPE,
            "target": None,
        },
    )
    tx_train = Node(
        "tx_train", "TransformDatasetUnit", {"scope": FULL_SCOPE, "target": None}
    )
    tx_test = Node(
        "tx_test", "TransformDatasetUnit", {"scope": FULL_SCOPE, "target": None}
    )
    # Saves back over the training data, so it needs the ref `dataset_path`
    # from the load as well as the live dataset from the transform: a join
    # whose two inputs live in different halves of the context.
    save_train = Node("save_train", "SaveDatasetUnit")
    save_test = Node(
        "save_test",
        "SaveDatasetToPathUnit",
        {"path": str(tmp_path / "out" / "dataset")},
    )

    nodes = [load_train, load_test, fit, tx_train, tx_test, save_train, save_test]
    edges = [
        *connect(load_train, fit),
        Edge("load_train", "dataset", "tx_train", "dataset"),
        Edge("load_train", "dataset_path", "save_train", "dataset_path"),
        *connect(fit, tx_train),
        *connect(fit, tx_test),
        Edge("load_test", "dataset", "tx_test", "dataset"),
        Edge("tx_train", "dataset", "save_train", "dataset"),
        *connect(tx_test, save_test),
    ]
    return Graph(nodes, edges)


def test_the_diamond_runs_and_the_fitted_state_survives_the_branch(
    stored_datasets, tmp_path
):
    """One fit, two branches, no refit.

    2.0 is only reachable if the converter fitted on the train branch reached
    the test branch still holding the range it learned, after crossing two
    context boundaries.
    """
    train, _ = stored_datasets

    run(_graph(tmp_path))

    assert _values(train / "dataset") == [0.0, 0.5, 1.0]
    assert _values(tmp_path / "out" / "dataset") == [2.0]


def test_two_loads_of_the_same_unit_do_not_fight_over_the_key(
    stored_datasets, tmp_path
):
    """Both loads write the fixed key ``dataset`` and neither is lost.

    This is what a shared context cannot do, and the reason each node gets one
    of its own.
    """
    train, _ = stored_datasets

    run(_graph(tmp_path))

    # A second load overwriting the first would have scaled the test value
    # against the test data's own range, giving 0.0.
    assert _values(tmp_path / "out" / "dataset") == [2.0]
    assert _values(train / "dataset") == [0.0, 0.5, 1.0]


def test_a_node_names_its_unit_and_the_engine_builds_one_instance_each(
    stored_datasets, tmp_path
):
    """Each node owns its instance, which is what per-instance state needs.

    A unit memoizes work on itself -- ``FitConverterUnit`` its converter
    class -- so two nodes sharing an instance would have the second silently
    run with the first one's.
    """
    a = instantiate(
        Node("a", "TransformDatasetUnit", {"scope": FULL_SCOPE, "target": None})
    )
    b = instantiate(
        Node("b", "TransformDatasetUnit", {"scope": FULL_SCOPE, "target": None})
    )

    assert a is not b
    assert type(a) is type(b) is TransformDatasetUnit


def test_the_execution_order_is_topological_not_the_order_given(
    stored_datasets, tmp_path
):
    """Order comes from the edges, not from the sequence the nodes arrived in.

    Its predecessor iterated the steps in whatever order the front sent them --
    creation order on the canvas -- and never read the edges it persisted.
    """
    graph = _graph(tmp_path)
    reversed_graph = Graph(list(reversed(graph.nodes)), graph.edges)

    order = validate(reversed_graph)

    assert order.index("load_train") < order.index("fit")
    assert order.index("fit") < order.index("tx_test")
    assert order.index("tx_train") < order.index("save_train")


def test_a_missing_input_is_caught_before_anything_runs(stored_datasets):
    save = Node("save", "SaveDatasetUnit")

    with pytest.raises(GraphError, match="requires 'dataset'"):
        validate(Graph([save], []))


def test_two_edges_into_one_port_are_rejected(stored_datasets, tmp_path):
    """The failure its predecessor had: a merge where the last writer wins."""
    graph = _graph(tmp_path)
    doubled = Graph(
        graph.nodes,
        [*graph.edges, Edge("load_test", "dataset", "tx_train", "dataset")],
    )

    with pytest.raises(GraphError, match="from 2 edges"):
        validate(doubled)


def test_a_cycle_is_reported(stored_datasets):
    a = Node("a", "TransformDatasetUnit", {"scope": FULL_SCOPE, "target": None})
    b = Node("b", "TransformDatasetUnit", {"scope": FULL_SCOPE, "target": None})
    cyclic = Graph(
        [a, b],
        [
            Edge("a", "dataset", "b", "dataset"),
            Edge("b", "dataset", "a", "dataset"),
        ],
    )

    with pytest.raises(GraphError, match="cycle"):
        validate(cyclic)


def test_an_edge_naming_a_key_the_unit_does_not_declare_is_rejected(
    stored_datasets, tmp_path
):
    graph = _graph(tmp_path)
    bogus = Graph(
        graph.nodes,
        [*graph.edges, Edge("load_train", "nonsense", "save_train", "dataset_path")],
    )

    with pytest.raises(GraphError, match="does not provide 'nonsense'"):
        validate(bogus)


def test_an_unknown_unit_name_is_rejected(stored_datasets):
    with pytest.raises(GraphError, match="no unit named 'Nope'"):
        validate(Graph([Node("x", "Nope")], []))


def test_a_registered_component_that_is_not_a_unit_is_rejected(stored_datasets):
    """The registry holds every kind of component, not only units."""
    with pytest.raises(GraphError, match="not a unit"):
        validate(Graph([Node("x", "NotAUnit")], []))


def test_duplicate_node_ids_are_rejected(stored_datasets, tmp_path):
    twice = Node("same", "SaveDatasetToPathUnit", {"path": str(tmp_path / "d")})
    with pytest.raises(GraphError, match="Duplicate node ids"):
        validate(Graph([twice, twice], []))


def test_every_problem_is_reported_at_once(stored_datasets):
    """A user fixing a graph wants the whole list, not one error per attempt."""
    graph = Graph(
        [Node("save", "SaveDatasetUnit"), Node("save", "SaveDatasetUnit")], []
    )

    with pytest.raises(GraphError) as caught:
        validate(graph)

    message = str(caught.value)
    assert "Duplicate node ids" in message
    assert "requires 'dataset'" in message


def test_moving_a_value_across_an_edge_keeps_the_half_it_came_from(
    stored_datasets, tmp_path
):
    """Refs travel as refs, live objects as live objects.

    ``dataset_path`` is a reference and ``dataset`` is a cached object, and the
    two have incompatible rules: a dataset handed to ``put_ref`` raises, and a
    reference handed to ``put`` drops the copy-on-read guarantee it depended
    on.
    """
    contexts = run(_graph(tmp_path))

    save_train = contexts["save_train"]
    assert save_train.origin("dataset_path") == "ref"
    assert save_train.origin("dataset") == "cache"


def test_a_context_is_released_once_nothing_downstream_reads_it(
    stored_datasets, tmp_path
):
    """Intermediate datasets do not stay alive for the length of the run."""
    graph = _graph(tmp_path)

    contexts = run(graph)

    assert set(contexts) == sinks(graph)
    assert "load_train" not in contexts


def test_artifacts_are_the_serializable_outputs_only(stored_datasets, tmp_path):
    """What gets recorded is the reference half of PROVIDES.

    The cache holds live datasets, models and tasks: not serializable, and
    always derivable again. So ``LoadDatasetUnit`` records the id and the path
    it published rather than the dataset itself, and ``TransformDatasetUnit``,
    whose only output is the live dataset, records nothing -- a real case, not
    a gap.
    """
    train, _ = stored_datasets
    sink = _RecordingSink()

    run(_graph(tmp_path), sink)

    recorded = {event[1]: event[2] for event in sink.events if event[0] == "finished"}

    assert set(recorded["load_train"]) == {"dataset_id", "dataset_path"}
    assert recorded["load_train"]["dataset_id"] == 7
    # Compared as a path, not as text: the unit joins with a forward slash and
    # Path renders a backslash on Windows.
    assert Path(recorded["load_train"]["dataset_path"]) == train / "dataset"
    assert recorded["tx_train"] == {}


def test_artifacts_of_reads_only_the_reference_half(stored_datasets):
    """The same rule, stated directly against a hand-built context."""
    ctx = ExecutionContext()
    ctx.put_ref("dataset_path", "/tmp/ds")
    ctx.put_ref("dataset_id", 7)
    ctx.put("dataset", object())

    assert artifacts_of(resolve_unit_class("LoadDatasetUnit"), ctx) == {
        "dataset_path": "/tmp/ds",
        "dataset_id": 7,
    }


def test_the_bundling_rule_picks_the_keys_two_nodes_agree_on(stored_datasets):
    """One drawn edge between two nodes stands for a set of keys."""
    fit = Node("fit", "FitConverterUnit", {})
    tx = Node("tx", "TransformDatasetUnit", {})

    assert connect(fit, tx) == (
        Edge("fit", "fitted_converter", "tx", "fitted_converter"),
    )


def test_a_node_belongs_to_itself_when_it_has_no_block():
    """Every node has a block, so the tracking never has a null to handle."""
    alone = Node("solo", "SaveDatasetUnit")
    grouped = Node("inner", "SaveDatasetUnit", {}, block_id="train-1")

    assert alone.block_id == "solo"
    assert grouped.block_id == "train-1"


class _RecordingSink(NullSink):
    """Records the notifications the engine sends, in order."""

    def __init__(self):
        self.events = []

    def run_started(self, order):
        self.events.append(("run_started", tuple(order)))

    def node_started(self, node_id, payload):
        self.events.append(("started", node_id, dict(payload)))

    def node_finished(self, node_id, artifacts, payload):
        self.events.append(("finished", node_id, dict(artifacts)))

    def node_failed(self, node_id, message):
        self.events.append(("failed", node_id))

    def nodes_cancelled(self, node_ids):
        self.events.append(("cancelled", tuple(node_ids)))

    def run_finished(self):
        self.events.append(("run_finished",))

    def run_failed(self, message):
        self.events.append(("run_failed",))


def test_the_sink_sees_every_node_start_and_finish(stored_datasets, tmp_path):
    sink = _RecordingSink()

    run(_graph(tmp_path), sink)

    kinds = [event[0] for event in sink.events]
    assert kinds[0] == "run_started"
    assert kinds[-1] == "run_finished"
    assert kinds.count("started") == 7
    assert kinds.count("finished") == 7
    assert "failed" not in kinds


def test_a_failing_node_cancels_everything_after_it(stored_datasets, tmp_path):
    """A run that died halfway must not look like one still in flight."""
    graph = _graph(tmp_path, converter="NoSuchConverter")
    sink = _RecordingSink()

    # The unit reports an unresolvable converter as a JobError, and the engine
    # lets it through rather than wrapping it: the message the user reads is
    # the unit's own.
    with pytest.raises(JobError, match="NoSuchConverter"):
        run(graph, sink)

    failed = [event for event in sink.events if event[0] == "failed"]
    cancelled = [event for event in sink.events if event[0] == "cancelled"]

    assert [event[1] for event in failed] == ["fit"]
    assert cancelled, "the nodes after the failure have to be reported"
    assert "tx_train" in cancelled[0][1]
    assert "save_test" in cancelled[0][1]
    assert ("run_failed",) in sink.events
    assert ("run_finished",) not in sink.events


def test_nothing_runs_when_the_graph_does_not_validate(stored_datasets, tmp_path):
    """Validation comes first, so a broken graph costs no work."""
    sink = _RecordingSink()
    save = Node("save", "SaveDatasetUnit")

    with pytest.raises(GraphError):
        run(Graph([save], []), sink)

    assert sink.events == []
