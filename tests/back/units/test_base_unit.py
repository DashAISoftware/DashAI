"""Tests for the atomic unit base class and its registration."""

import pytest

from DashAI.back.dependencies.registry import ComponentRegistry
from DashAI.back.units.base_unit import BaseUnit
from DashAI.back.units.context import ExecutionContext, UnitContractError


class DummyUnit(BaseUnit):
    """Unit that copies a required key into a provided one."""

    REQUIRES = ("dataset",)
    PROVIDES = ("x",)

    def execute(self, ctx: ExecutionContext) -> None:
        ctx.put("x", f"prepared {ctx.require('dataset')}")


class LyingUnit(BaseUnit):
    """Unit that declares an output it never writes."""

    PROVIDES = ("x",)

    def execute(self, ctx: ExecutionContext) -> None:
        pass


class ValidatingUnit(BaseUnit):
    """Unit that rejects its configuration before running."""

    def __init__(self, **config) -> None:
        super().__init__(**config)
        self.validate_calls = 0

    def validate(self, ctx: ExecutionContext) -> None:
        self.validate_calls += 1
        if not self.config.get("allowed", True):
            raise ValueError("not allowed")

    def execute(self, ctx: ExecutionContext) -> None:
        ctx.put("ran", True)


def test_unit_stores_its_configuration():
    unit = DummyUnit(dataset_id=3, columns=["a"])

    assert unit.config == {"dataset_id": 3, "columns": ["a"]}


def test_unit_runs_and_writes_its_output():
    ctx = ExecutionContext()
    ctx.put("dataset", "a dataset")

    DummyUnit()(ctx)

    assert ctx.require("x") == "prepared a dataset"


def test_unit_refuses_to_run_without_its_required_keys():
    ctx = ExecutionContext()

    with pytest.raises(UnitContractError, match="'dataset' is not available"):
        DummyUnit()(ctx)


def test_unit_fails_when_it_does_not_deliver_what_it_promised():
    ctx = ExecutionContext()

    with pytest.raises(UnitContractError, match="'x' is not available"):
        LyingUnit()(ctx)


def test_validate_is_a_noop_by_default():
    DummyUnit().validate(ExecutionContext())


def test_validate_can_reject_a_configuration_without_executing():
    ctx = ExecutionContext()
    unit = ValidatingUnit(allowed=False)

    with pytest.raises(ValueError, match="not allowed"):
        unit.validate(ctx)

    assert not ctx.has("ran")


def test_call_invokes_validate_automatically_before_execute():
    """Regression: ``unit(ctx)`` alone must run validate(), not just execute().

    Before this fix a unit's ``validate`` (e.g. ``BuildModelUnit``'s download
    gate) only ran if the caller remembered to invoke it separately — an easy
    step to forget for any future caller that just does ``unit(ctx)``, the one
    call the base class marks as the sanctioned entry point.
    """
    ctx = ExecutionContext()
    unit = ValidatingUnit(allowed=True)

    unit(ctx)

    assert unit.validate_calls == 1
    assert ctx.require("ran") is True


def test_call_stops_at_validate_and_never_reaches_execute():
    ctx = ExecutionContext()
    unit = ValidatingUnit(allowed=False)

    with pytest.raises(ValueError, match="not allowed"):
        unit(ctx)

    assert not ctx.has("ran")


def test_units_register_under_their_own_registry_type():
    """The registry derives TYPE by walking the MRO for a single "Base"
    ancestor declaring it. BaseUnit must be that single candidate."""
    registry = ComponentRegistry(initial_components=[DummyUnit])

    assert registry["DummyUnit"]["type"] == "Unit"
    assert [c["name"] for c in registry.get_components_by_types(select="Unit")] == [
        "DummyUnit"
    ]


def test_registered_units_are_configurable_objects_with_a_schema():
    registry = ComponentRegistry(initial_components=[DummyUnit])

    component = registry["DummyUnit"]

    assert component["configurable_object"] is True
    assert component["schema"] is not None
