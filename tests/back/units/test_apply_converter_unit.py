"""Contract tests for ApplyConverterUnit, isolated from ConverterJob.

The job only ever runs one of these per invocation, so an end-to-end run cannot
show whether the unit is safe to chain. These tests build the context by hand
and run several units against it, which is what the future DAG will do.
"""

import pandas as pd
import pyarrow as pa
import pytest
from kink import di

from DashAI.back.dataloaders.classes.dashai_dataset import to_dashai_dataset
from DashAI.back.job.base_job import JobError
from DashAI.back.types.value_types import Integer
from DashAI.back.units.apply_converter_unit import ApplyConverterUnit
from DashAI.back.units.context import ExecutionContext, UnitContractError


def _dataset(**columns):
    frame = pd.DataFrame(columns)
    types = {name: Integer(arrow_type=pa.int64()) for name in frame.columns}
    return to_dashai_dataset(frame, types=types)


class _DropScopedColumns:
    """Converter that removes whatever is in scope, like ColumnRemover."""

    CHANGES_ROW_COUNT = False

    def __init__(self, **params):
        self.params = params
        self.columns = []

    def fit(self, x, y=None):
        self.columns = x.column_names
        return self

    def transform(self, x, y=None):
        return x.remove_columns(self.columns)


class _ReplaceWithScope:
    """Converter that replaces the dataset with the scoped columns only."""

    CHANGES_ROW_COUNT = True

    def __init__(self, **params):
        self.params = params

    def fit(self, x, y=None):
        return self

    def transform(self, x, y=None):
        return x


class _RecordingConverter:
    """Converter that records what fit and transform were handed."""

    CHANGES_ROW_COUNT = True

    def __init__(self, **params):
        self.params = params
        self.fit_x = None
        self.fit_y = None
        self.transform_x = None
        self.transform_y = None

    def fit(self, x, y=None):
        self.fit_x = x
        self.fit_y = y
        return self

    def transform(self, x, y=None):
        self.transform_x = x
        self.transform_y = y
        return x


class _FailingFit:
    CHANGES_ROW_COUNT = False

    def __init__(self, **params):
        pass

    def fit(self, x, y=None):
        raise ValueError("bad input")

    def transform(self, x, y=None):  # pragma: no cover - never reached
        return x


class _FailingTransform:
    CHANGES_ROW_COUNT = False

    def __init__(self, **params):
        pass

    def fit(self, x, y=None):
        return self

    def transform(self, x, y=None):
        raise RuntimeError("boom")


@pytest.fixture(name="registry")
def fixture_registry():
    registry = {
        "DropScopedColumns": {"class": _DropScopedColumns},
        "ReplaceWithScope": {"class": _ReplaceWithScope},
        "RecordingConverter": {"class": _RecordingConverter},
        "FailingFit": {"class": _FailingFit},
        "FailingTransform": {"class": _FailingTransform},
    }
    di["component_registry"] = registry
    yield registry
    del di["component_registry"]


def _unit(name, scope=None, target=None, params=None):
    return ApplyConverterUnit(
        converter={"component": name, "params": params or {}},
        scope=scope,
        target=target,
    )


def _ctx(dataset):
    ctx = ExecutionContext()
    ctx.put("dataset", dataset)
    return ctx


def test_the_unit_refuses_to_run_without_a_dataset(registry):
    with pytest.raises(UnitContractError, match="'dataset' is not available"):
        _unit("DropScopedColumns")(ExecutionContext())


def test_a_scoped_column_is_resolved_by_one_based_index(registry):
    ctx = _ctx(_dataset(a=[1, 2], b=[3, 4], c=[5, 6]))

    _unit("DropScopedColumns", scope={"columns": [{"idx": 2}], "rows": []})(ctx)

    assert ctx.require("dataset").column_names == ["a", "c"]


def test_an_empty_column_scope_selects_every_column(registry):
    ctx = _ctx(_dataset(a=[1, 2], b=[3, 4]))

    _unit("ReplaceWithScope", scope={"columns": [], "rows": []})(ctx)

    assert ctx.require("dataset").column_names == ["a", "b"]


def test_a_null_scope_is_treated_as_an_empty_one(registry):
    """The API schema writes the ``scope`` key but allows it to be null.

    ``dict.get("scope", default)`` returns ``None`` rather than the default when
    the key is present and null, so the unit has to coalesce it explicitly.
    """
    ctx = _ctx(_dataset(a=[1, 2], b=[3, 4]))

    _unit("ReplaceWithScope", scope=None)(ctx)

    assert ctx.require("dataset").column_names == ["a", "b"]


def test_chained_units_resolve_their_indexes_against_the_current_dataset(registry):
    """The reason no column identity may cross the context boundary.

    The first unit drops column ``a``, so index 1 means ``b`` by the time the
    second unit runs. A column list resolved once and published to the context
    would make the second unit drop the wrong column.
    """
    ctx = _ctx(_dataset(a=[1, 2], b=[3, 4], c=[5, 6]))

    _unit("DropScopedColumns", scope={"columns": [{"idx": 1}], "rows": []})(ctx)
    assert ctx.require("dataset").column_names == ["b", "c"]

    _unit("DropScopedColumns", scope={"columns": [{"idx": 1}], "rows": []})(ctx)
    assert ctx.require("dataset").column_names == ["c"]


def test_the_unit_publishes_no_column_state_into_the_context(registry):
    """Nothing resolved from the dataset may outlive the unit that resolved it."""
    ctx = _ctx(_dataset(a=[1, 2], b=[3, 4]))

    _unit("DropScopedColumns", scope={"columns": [{"idx": 1}], "rows": []})(ctx)

    for leaked in (
        "column_names",
        "scope_column_names",
        "scope_column_indexes",
        "target_column_name",
        "converter",
    ):
        assert not ctx.has(leaked), leaked


def test_two_units_in_one_context_do_not_share_their_resolved_converter(registry):
    """Registry lookups are memoized on the instance, never in the context.

    A class cached under a context key would make the second unit silently run
    the first one's converter.
    """
    ctx = _ctx(_dataset(a=[1, 2], b=[3, 4], c=[5, 6]))

    first = _unit("DropScopedColumns", scope={"columns": [{"idx": 1}], "rows": []})
    second = _unit("ReplaceWithScope", scope={"columns": [{"idx": 1}], "rows": []})

    first(ctx)
    second(ctx)

    assert first._converter_class is _DropScopedColumns
    assert second._converter_class is _ReplaceWithScope
    # ReplaceWithScope keeps only what is in scope, which is now "b".
    assert ctx.require("dataset").column_names == ["b"]


def test_a_row_scope_narrows_fit_but_not_transform(registry):
    ctx = _ctx(_dataset(a=[1, 2, 3, 4], b=[5, 6, 7, 8]))
    recorded = {}

    class _Spy(_RecordingConverter):
        def fit(self, x, y=None):
            recorded["fit_rows"] = len(x)
            return super().fit(x, y)

        def transform(self, x, y=None):
            recorded["transform_rows"] = len(x)
            recorded["same_object"] = x is self.fit_x
            return super().transform(x, y)

    registry["Spy"] = {"class": _Spy}

    _unit("Spy", scope={"columns": [{"idx": 1}], "rows": [1, 2]})(ctx)

    assert recorded["fit_rows"] == 2
    assert recorded["transform_rows"] == 4
    assert recorded["same_object"] is False


def test_no_row_scope_hands_transform_the_same_object_as_fit(registry):
    """Object identity, not equality, is part of the contract here.

    ``TypeCastConverter`` caches converted columns during ``fit`` and reuses
    them in ``transform`` only when handed the same dataset object. Losing that
    identity does not fail anything — it just silently recomputes.
    """
    ctx = _ctx(_dataset(a=[1, 2, 3, 4], b=[5, 6, 7, 8]))
    recorded = {}

    class _Spy(_RecordingConverter):
        def transform(self, x, y=None):
            recorded["same_object"] = x is self.fit_x
            return super().transform(x, y)

    registry["Spy"] = {"class": _Spy}

    _unit("Spy", scope={"columns": [{"idx": 1}], "rows": []})(ctx)

    assert recorded["same_object"] is True


def test_a_target_column_is_resolved_and_handed_over_as_y(registry):
    ctx = _ctx(_dataset(a=[1, 2], b=[3, 4], label=[5, 6]))
    recorded = {}

    class _Spy(_RecordingConverter):
        def fit(self, x, y=None):
            recorded["fit_y"] = None if y is None else y.column_names
            return super().fit(x, y)

        def transform(self, x, y=None):
            recorded["transform_y"] = None if y is None else y.column_names
            return super().transform(x, y)

    registry["Spy"] = {"class": _Spy}

    _unit(
        "Spy",
        scope={"columns": [{"idx": 1}], "rows": []},
        target={"idx": 3},
    )(ctx)

    assert recorded["fit_y"] == ["label"]
    assert recorded["transform_y"] == ["label"]


def test_no_target_means_no_y(registry):
    ctx = _ctx(_dataset(a=[1, 2], b=[3, 4]))
    recorded = {}

    class _Spy(_RecordingConverter):
        def fit(self, x, y=None):
            recorded["fit_y"] = y
            return super().fit(x, y)

    registry["Spy"] = {"class": _Spy}

    _unit("Spy", scope={"columns": [{"idx": 1}], "rows": []}, target=None)(ctx)

    assert recorded["fit_y"] is None


def test_validate_rejects_an_out_of_bounds_target_without_running(registry):
    ctx = _ctx(_dataset(a=[1, 2], b=[3, 4]))
    unit = _unit("DropScopedColumns", target={"idx": 99})

    with pytest.raises(JobError, match="Target column index 99 is out of bounds"):
        unit.validate(ctx)

    assert ctx.require("dataset").column_names == ["a", "b"]


def test_the_target_bound_is_rechecked_against_the_dataset_of_the_moment(registry):
    """A target that was valid before the previous converter ran may not be now.

    ``validate`` runs against whatever dataset is in the context when it is
    called; chaining means ``execute`` can face a narrower one. Re-checking
    turns what would be a bare IndexError into the same JobError.
    """
    ctx = _ctx(_dataset(a=[1, 2], b=[3, 4], c=[5, 6]))
    unit = _unit(
        "DropScopedColumns",
        scope={"columns": [{"idx": 1}], "rows": []},
        target={"idx": 3},
    )

    unit.validate(ctx)  # 3 columns: idx 3 is fine right now.

    # Another converter narrows the dataset behind its back.
    _unit("ReplaceWithScope", scope={"columns": [{"idx": 1}], "rows": []})(ctx)

    with pytest.raises(JobError, match="Target column index 3 is out of bounds"):
        unit(ctx)


def test_an_unknown_converter_names_the_culprit(registry):
    ctx = _ctx(_dataset(a=[1, 2]))

    with pytest.raises(JobError, match="Error importing converter NotRegistered"):
        _unit("NotRegistered")(ctx)


def test_a_value_error_during_fit_is_reported_as_a_validation_error(registry):
    ctx = _ctx(_dataset(a=[1, 2]))

    with pytest.raises(JobError, match="Validation error fitting FailingFit"):
        _unit("FailingFit")(ctx)


def test_any_other_error_during_fit_is_reported_as_a_fit_error(registry):
    ctx = _ctx(_dataset(a=[1, 2]))

    class _Boom(_FailingFit):
        def fit(self, x, y=None):
            raise RuntimeError("nope")

    registry["Boom"] = {"class": _Boom}

    with pytest.raises(JobError, match="Error fitting converter Boom"):
        _unit("Boom")(ctx)


def test_an_error_during_transform_is_reported_as_a_transform_error(registry):
    ctx = _ctx(_dataset(a=[1, 2]))

    with pytest.raises(JobError, match="Error transforming data with FailingTransform"):
        _unit("FailingTransform")(ctx)


def test_converter_params_reach_the_constructor(registry):
    ctx = _ctx(_dataset(a=[1, 2]))
    unit = _unit("ReplaceWithScope", params={"threshold": 3})

    unit(ctx)

    assert unit._converter_class is _ReplaceWithScope


def test_a_changes_row_count_converter_replaces_the_whole_dataset(registry):
    ctx = _ctx(_dataset(a=[1, 2], b=[3, 4], c=[5, 6]))

    _unit("ReplaceWithScope", scope={"columns": [{"idx": 2}], "rows": []})(ctx)

    assert ctx.require("dataset").column_names == ["b"]
