"""Tests for the execution context shared between atomic units."""

import pytest

from DashAI.back.units.context import ExecutionContext, UnitContractError


def test_put_ref_stores_a_serializable_value():
    ctx = ExecutionContext()
    ctx.put_ref("run_id", 5)

    assert ctx.get("run_id") == 5
    assert ctx.refs == {"run_id": 5}


def test_put_ref_rejects_a_non_serializable_value():
    ctx = ExecutionContext()

    with pytest.raises(UnitContractError, match="not JSON serializable"):
        ctx.put_ref("model", object())


def test_constructor_validates_the_initial_refs():
    with pytest.raises(UnitContractError, match="not JSON serializable"):
        ExecutionContext(refs={"model": object()})


def test_put_accepts_a_live_object():
    ctx = ExecutionContext()
    sentinel = object()
    ctx.put("model", sentinel)

    assert ctx.get("model") is sentinel
    assert ctx.refs == {}


def test_get_prefers_the_cache_over_the_refs():
    ctx = ExecutionContext(refs={"model_path": "/on/disk"})
    ctx.put("model_path", "/in/memory")

    assert ctx.get("model_path") == "/in/memory"


def test_get_falls_back_to_the_refs_and_then_the_default():
    ctx = ExecutionContext(refs={"dataset_id": 3})

    assert ctx.get("dataset_id") == 3
    assert ctx.get("missing") is None
    assert ctx.get("missing", "fallback") == "fallback"


def test_require_returns_the_value_when_present():
    ctx = ExecutionContext(refs={"run_id": 7})
    ctx.put("model", "a model")

    assert ctx.require("run_id") == 7
    assert ctx.require("model") == "a model"


def test_require_raises_and_lists_the_present_keys():
    ctx = ExecutionContext(refs={"run_id": 7})
    ctx.put("model", "a model")

    with pytest.raises(UnitContractError) as exc_info:
        ctx.require("x")

    message = str(exc_info.value)
    assert "'x' is not available" in message
    assert "'model'" in message
    assert "'run_id'" in message


def test_has_checks_both_halves():
    ctx = ExecutionContext(refs={"run_id": 7})
    ctx.put("model", "a model")

    assert ctx.has("run_id")
    assert ctx.has("model")
    assert not ctx.has("x")


def test_clear_cache_drops_live_objects_and_keeps_refs():
    ctx = ExecutionContext(refs={"run_id": 7})
    ctx.put("model", "a model")

    ctx.clear_cache()

    assert not ctx.has("model")
    assert ctx.require("run_id") == 7


def test_refs_property_returns_a_copy():
    ctx = ExecutionContext(refs={"run_id": 7})

    ctx.refs["run_id"] = 99

    assert ctx.require("run_id") == 7


def test_round_trip_through_to_dict_keeps_refs_and_drops_the_cache():
    ctx = ExecutionContext(
        refs={"run_id": 7, "split_indexes": {"train_indexes": [0, 1]}}
    )
    ctx.put("model", object())

    restored = ExecutionContext.from_dict(ctx.to_dict())

    assert restored.require("run_id") == 7
    assert restored.require("split_indexes") == {"train_indexes": [0, 1]}
    assert not restored.has("model")


def test_to_dict_is_detached_from_the_context():
    ctx = ExecutionContext(refs={"run_id": 7})

    serialized = ctx.to_dict()
    serialized["run_id"] = 99

    assert ctx.require("run_id") == 7


def test_put_ref_isolates_from_later_mutation_of_the_original_object():
    """Regression: ``put_ref`` must not alias a caller's mutable dict.

    ``BuildModelUnit`` passes ``run.parameters`` — the dict SQLAlchemy attaches
    to the ``Run`` row — straight into ``put_ref``. Without a defensive copy,
    a later in-place edit reachable through the context (e.g.
    ``ModelFactory.update_parameters`` rewriting a nested ``fixed_value``
    during hyperparameter search) would silently write through into the ORM
    object, corrupting ``run.parameters`` before it was ever meant to change.
    """
    original = {"n_estimators": {"fixed_value": 2}}
    ctx = ExecutionContext()
    ctx.put_ref("model_parameters", original)

    original["n_estimators"]["fixed_value"] = 999

    assert ctx.require("model_parameters")["n_estimators"]["fixed_value"] == 2


def test_require_returns_an_isolated_copy_of_a_reference():
    ctx = ExecutionContext(
        refs={"model_parameters": {"n_estimators": {"fixed_value": 2}}}
    )

    fetched = ctx.require("model_parameters")
    fetched["n_estimators"]["fixed_value"] = 999

    assert ctx.require("model_parameters")["n_estimators"]["fixed_value"] == 2


def test_get_returns_an_isolated_copy_of_a_reference():
    ctx = ExecutionContext(
        refs={"model_parameters": {"n_estimators": {"fixed_value": 2}}}
    )

    fetched = ctx.get("model_parameters")
    fetched["n_estimators"]["fixed_value"] = 999

    assert ctx.get("model_parameters")["n_estimators"]["fixed_value"] == 2


def test_cached_live_objects_are_still_returned_by_reference():
    """The copy-on-read fix must only apply to refs, never to the cache.

    A model, an in-memory dataset, an open session — these have to be the
    same live object on every ``get``/``require``. Deep-copying them would
    silently break training (the model you fit is not the model you saved)
    while looking, from the outside, like nothing went wrong.
    """

    class LiveThing:
        pass

    live_object = LiveThing()
    ctx = ExecutionContext()
    ctx.put("model", live_object)

    assert ctx.get("model") is live_object
    assert ctx.require("model") is live_object


def test_origin_says_which_half_a_key_is_in():
    ctx = ExecutionContext(refs={"dataset_path": "/tmp/ds"})
    ctx.put("dataset", object())

    assert ctx.origin("dataset_path") == "ref"
    assert ctx.origin("dataset") == "cache"
    assert ctx.origin("nothing_here") is None


def test_origin_prefers_the_cache_the_same_way_get_does():
    """One key in both halves has to have one answer, not two.

    ``get`` and ``require`` read the cache first, so anything deciding how to
    move a value has to agree with them or the value would be read from one
    half and written as if it came from the other.
    """
    live = object()
    ctx = ExecutionContext(refs={"x": 1})
    ctx.put("x", live)

    assert ctx.origin("x") == "cache"
    assert ctx.get("x") is live
    assert ctx.require("x") is live


def test_origin_does_not_copy_the_reference_half():
    """The reason the method exists: asking must not cost a deep copy.

    ``key in ctx.refs`` answers the same question, but ``refs`` returns a deep
    copy of every reference the context holds, so asking once per edge of a
    graph would copy the whole reference half once per edge.
    """
    ctx = ExecutionContext(refs={"nested": {"deep": [1, 2, 3]}})
    inner = ctx._refs["nested"]

    assert ctx.origin("nested") == "ref"
    assert ctx._refs["nested"] is inner
