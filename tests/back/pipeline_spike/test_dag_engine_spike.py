"""Runs real units as a DAG, to find out what the unit contract cannot express.

The graph below is the train/test converter flow, which is the smallest thing a
single shared context genuinely cannot run: two ``LoadDatasetUnit`` instances
both write the fixed key ``dataset``, so in one context the second load erases
the first. Section 9 of ATOMIZING_JOBS.md proposes giving each node a context of
its own and putting the renaming on the edge; these tests check whether that
actually works with the units exactly as they are.

    load_train --dataset--+-------------------> tx_train --dataset--> save_train
                          |                        ^                    ^
                          +-> fit --converter--+---+       dataset_path  |
                                               |                         --+
    load_test --dataset------------------------|-> tx_test --dataset--> save_test

Two fan-outs (``load_train`` feeds two nodes, ``fit`` feeds two nodes) and two
joins (each ``tx`` node takes a dataset from one branch and a fitted converter
from another). The number that proves it worked is 2.0: MinMaxScaler fitted on
train [0, 5, 10] learns min=0 max=10, so a test value of 20 scales to 2.0. A
refit on the test data would have produced 0.0 instead.
"""

import pandas as pd
import pyarrow as pa
import pytest
from kink import di

from DashAI.back.converters.scikit_learn.min_max_scaler import MinMaxScaler
from DashAI.back.dataloaders.classes.dashai_dataset import (
    load_dataset,
    save_dataset,
    to_dashai_dataset,
)
from DashAI.back.types.value_types import Float
from DashAI.back.units.apply_converter_unit import ApplyConverterUnit
from DashAI.back.units.fit_converter_unit import FitConverterUnit
from DashAI.back.units.load_dataset_unit import LoadDatasetUnit
from DashAI.back.units.prepare_and_split_unit import PrepareAndSplitUnit
from DashAI.back.units.save_dataset_to_path_unit import SaveDatasetToPathUnit
from DashAI.back.units.save_dataset_unit import SaveDatasetUnit
from DashAI.back.units.save_model_unit import SaveModelUnit
from DashAI.back.units.transform_dataset_unit import TransformDatasetUnit
from tests.back.pipeline_spike.dag_engine import (
    Edge,
    Graph,
    GraphError,
    Node,
    connect,
    run,
    sinks,
    validate,
)

FULL_SCOPE = {"columns": [], "rows": []}
_MIN_MAX = {"component": "MinMaxScaler", "params": {}}


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
    """Dataset 7 is the training data, dataset 8 the test data."""
    train = _write(tmp_path / "train", a=[0.0, 5.0, 10.0])
    test = _write(tmp_path / "test", a=[20.0])

    di["session_factory"] = _FakeSessionFactory(
        {"Dataset": {7: _Row(str(train)), 8: _Row(str(test))}}
    )
    di["component_registry"] = {"MinMaxScaler": {"class": MinMaxScaler}}
    yield train, test
    del di["session_factory"]
    del di["component_registry"]


def _graph(tmp_path, converter="MinMaxScaler"):
    """The diamond, wired with the bundling rule wherever it applies."""
    load_train = Node("load_train", LoadDatasetUnit(dataset_id=7))
    load_test = Node("load_test", LoadDatasetUnit(dataset_id=8))
    fit = Node(
        "fit",
        FitConverterUnit(
            converter={"component": converter, "params": {}},
            scope=FULL_SCOPE,
            target=None,
        ),
    )
    tx_train = Node("tx_train", TransformDatasetUnit(scope=FULL_SCOPE, target=None))
    tx_test = Node("tx_test", TransformDatasetUnit(scope=FULL_SCOPE, target=None))
    # Saves back over the training data, so it needs the ref `dataset_path` from
    # the load as well as the live dataset from the transform: a join whose two
    # inputs live in different halves of the context.
    save_train = Node("save_train", SaveDatasetUnit())
    save_test = Node(
        "save_test", SaveDatasetToPathUnit(path=str(tmp_path / "out" / "dataset"))
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
    """The headline case: one fit, two branches, no refit.

    2.0 on the test branch is only reachable if the converter fitted in the
    ``fit`` node arrived at ``tx_test`` still carrying the range it learned from
    the training data, having crossed two context boundaries on the way.
    """
    train, _test = stored_datasets

    run(_graph(tmp_path))

    assert _values(train / "dataset") == [0.0, 0.5, 1.0]
    assert _values(tmp_path / "out" / "dataset") == [2.0]


def test_two_loads_of_the_same_unit_do_not_fight_over_the_key(
    stored_datasets, tmp_path
):
    """Section 9's proposal, checked directly.

    Both loads publish the fixed key ``dataset``. In one shared context the
    second would overwrite the first and the test branch would silently scale
    the training data.
    """
    graph = _graph(tmp_path)
    contexts = run(graph)

    assert sinks(graph) == {"save_train", "save_test"}
    # Every context still alive at the end belongs to a sink; the loads and the
    # fit were dropped as soon as nothing needed them.
    assert set(contexts) == {"save_train", "save_test"}


def test_the_engine_never_needed_a_shared_key_to_be_renamed_by_a_unit(tmp_path):
    """The edge does the renaming; the units keep their fixed key names."""
    graph = _graph(tmp_path)

    assert set(validate(graph)[:2]) == {"load_train", "load_test"}
    assert all(edge.src_key == edge.dst_key for edge in graph.edges)


def test_the_bundling_rule_picks_the_keys_two_nodes_agree_on():
    """One drawn edge between two nodes stands for a set of keys."""
    load = Node("load", LoadDatasetUnit(dataset_id=1))
    save = Node("save", SaveDatasetUnit())

    assert {edge.src_key for edge in connect(load, save)} == {"dataset", "dataset_path"}


def test_a_missing_input_is_caught_before_anything_runs():
    tx = Node("tx", TransformDatasetUnit(scope=FULL_SCOPE, target=None))
    load = Node("load", LoadDatasetUnit(dataset_id=1))

    with pytest.raises(GraphError, match="tx requires 'fitted_converter'"):
        validate(Graph([load, tx], list(connect(load, tx))))


def test_two_edges_into_one_port_are_rejected():
    """The failure the old engine had: a merge where the last writer wins."""
    load_a = Node("a", LoadDatasetUnit(dataset_id=1))
    load_b = Node("b", LoadDatasetUnit(dataset_id=2))
    fit = Node(
        "fit",
        FitConverterUnit(converter=_MIN_MAX, scope=FULL_SCOPE, target=None),
    )
    graph = Graph([load_a, load_b, fit], [*connect(load_a, fit), *connect(load_b, fit)])

    with pytest.raises(GraphError, match="fit gets 'dataset' from 2 sources"):
        validate(graph)


def test_a_cycle_is_reported():
    fit = Node(
        "fit",
        FitConverterUnit(converter=_MIN_MAX, scope=FULL_SCOPE, target=None),
    )
    tx = Node("tx", TransformDatasetUnit(scope=FULL_SCOPE, target=None))
    graph = Graph([fit, tx], [*connect(fit, tx), *connect(tx, fit)])

    with pytest.raises(GraphError, match="cycle"):
        validate(graph)


def test_run_id_is_no_longer_an_orphan_input():
    """``run_id`` used to be a context key no unit published.

    Four units required it and none provided it, so a graph had to inject it
    from outside and the validator could not tell that injection apart from a
    wire the user forgot to draw. It was never data flowing through the graph:
    in a job it arrived through ``self.kwargs``.

    It is configuration now, which is what closed that hole. Every key left in
    ``REQUIRES`` has a unit that publishes it, so "nothing supplies this" means
    a missing edge and nothing else. The seeds mechanism this spike used for it
    has no remaining caller.
    """
    save = Node("save", SaveModelUnit(artifact_prefix="pipeline-1-save"))

    with pytest.raises(GraphError, match="save requires 'model'"):
        validate(Graph([save], []))

    assert "run_id" not in SaveModelUnit.REQUIRES


def test_a_seed_for_a_key_the_unit_never_uses_is_rejected():
    save = Node(
        "save",
        SaveModelUnit(artifact_prefix="pipeline-1-save"),
        seeds={"nonsense": 2},
    )

    with pytest.raises(GraphError, match="seeded with 'nonsense'"):
        validate(Graph([save], []))


def test_an_optional_output_cannot_be_wired_at_all():
    """``PROVIDES`` is the whole vocabulary an edge can name.

    ``FitModelUnit`` produces ``best_parameters`` only on the hyperparameter
    search branch, so it cannot declare it (``__call__`` checks ``PROVIDES``
    unconditionally). ``ModelJob`` copes by reading it with ``ctx.has(...)``.
    A graph cannot: a key outside ``PROVIDES`` is not addressable by an edge,
    so the limitation goes from "not verifiable" to "not connectable".
    """
    fit = Node(
        "fit",
        FitConverterUnit(converter=_MIN_MAX, scope=FULL_SCOPE, target=None),
    )
    tx = Node("tx", TransformDatasetUnit(scope=FULL_SCOPE, target=None))
    graph = Graph([fit, tx], [Edge("fit", "best_parameters", "tx", "dataset")])

    with pytest.raises(GraphError, match="fit does not provide 'best_parameters'"):
        validate(graph)


def test_a_key_a_middle_node_does_not_republish_needs_an_edge_around_it():
    """A converter in the middle does not carry the ids the load published.

    ``ApplyConverterUnit`` provides only ``dataset`` and ``fitted_converter``,
    and it is right not to republish ``dataset_id`` -- section 4.3 forbids
    anything derived from the object being transformed from crossing the
    boundary. But ``PrepareAndSplitUnit`` downstream needs both, so ``dataset``
    comes through the converter and ``dataset_id`` has to jump over it.

    The engine accepts the bypass. What it costs is on the canvas: the user has
    to draw an arrow from the loader past the converters to the split.
    """
    load = Node("load", LoadDatasetUnit(dataset_id=1))
    apply_ = Node(
        "apply",
        ApplyConverterUnit(converter=_MIN_MAX, scope=FULL_SCOPE, target=None),
    )
    split = Node("split", PrepareAndSplitUnit(splitter={}))

    bundled = Graph(
        [load, apply_, split], [*connect(load, apply_), *connect(apply_, split)]
    )
    with pytest.raises(GraphError, match="split requires 'dataset_id'"):
        validate(bundled)

    bypassed = Graph(
        [load, apply_, split],
        [
            *connect(load, apply_),
            *connect(apply_, split),
            Edge("load", "dataset_id", "split", "dataset_id"),
        ],
    )
    assert validate(bypassed) == ["load", "apply", "split"]


class _CountingConverter:
    """Records how many times it was asked to transform, and who built it."""

    instances = []
    CHANGES_ROW_COUNT = False

    def __init__(self, **params):
        _CountingConverter.instances.append(self)
        self.transform_calls = 0

    def fit(self, x, y=None):
        return self

    def transform(self, x, y=None):
        self.transform_calls += 1
        return x


def test_a_fan_out_hands_both_branches_the_same_live_object(stored_datasets, tmp_path):
    """Identity survives the fan-out, which it has to (ATOMIZING_JOBS 5.7).

    Some converters cache against the object they were given, so a copy would
    silently recompute. It also means two consumers of one fitted converter
    share mutable state -- harmless while the engine is sequential, and a
    reason to keep it that way.
    """
    _CountingConverter.instances.clear()
    di["component_registry"]["Counting"] = {"class": _CountingConverter}

    graph = _graph(tmp_path, converter="Counting")
    run(graph)

    assert len(_CountingConverter.instances) == 1
    assert _CountingConverter.instances[0].transform_calls == 2


def test_moving_a_value_across_an_edge_keeps_the_half_it_came_from(
    stored_datasets, tmp_path
):
    """Refs travel as refs, live objects as live objects.

    ``dataset_path`` is a ref and ``dataset`` is a cached object, and the two
    have incompatible rules: ``put_ref`` validates with ``json.dumps``, so a
    dataset sent that way raises, and ``put`` would drop the copy-on-write
    guarantee a ref depends on. The engine has to ask which half a key is in --
    and the only public way to ask deep-copies the entire reference half, once
    per edge.
    """
    from tests.back.pipeline_spike import dag_engine

    graph = _graph(tmp_path)
    dag_engine.REF_PROBES[0] = 0
    contexts = run(graph)

    assert dag_engine.REF_PROBES[0] == len(graph.edges)
    save_train = contexts["save_train"]
    assert "dataset_path" in save_train.refs
    assert "dataset" not in save_train.refs
    assert save_train.has("dataset")
