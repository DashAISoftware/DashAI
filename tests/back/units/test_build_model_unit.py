"""Tests for BuildModelUnit's model-class resolution and its caching."""

import pytest
from kink import di

from DashAI.back.units.build_model_unit import BuildModelUnit
from DashAI.back.units.context import ExecutionContext


class _ModelA:
    def __init__(self, **kwargs):
        pass


class _ModelB:
    def __init__(self, **kwargs):
        pass


@pytest.fixture
def fake_registry():
    """A minimal dict-shaped registry: enough for name -> class lookups."""
    registry = {
        "ModelA": {"class": _ModelA},
        "ModelB": {"class": _ModelB},
    }
    di["component_registry"] = registry
    yield registry
    del di["component_registry"]


def _build_unit(model_name, run_id=1):
    return BuildModelUnit(
        model={"component": model_name, "params": {}},
        train_metrics=[],
        validation_metrics=[],
        test_metrics=[],
        run_id=run_id,
    )


def test_two_build_model_units_in_one_context_resolve_independently(fake_registry):
    """Regression: the model-class cache must not be keyed by the context.

    Two ``BuildModelUnit`` instances configured for different models, run
    against the same context, must each build their own model. Before this
    fix the class was memoized under a context-global ``"model_class"`` key,
    so the second unit would silently reuse the first one's resolved class —
    and its download-gate check would validate the wrong model too.
    """
    ctx = ExecutionContext()
    ctx.put("x", {"train": None, "validation": None})
    ctx.put("y", {"train": None, "validation": None})
    ctx.put("n_labels", None)
    ctx.put_ref("task_name", "ATask")

    a = _build_unit("ModelA")
    a(ctx)
    model_a = ctx.get("model")

    b = _build_unit("ModelB")
    b(ctx)
    model_b = ctx.get("model")

    assert isinstance(model_a, _ModelA)
    assert isinstance(model_b, _ModelB)


def test_resolve_model_class_is_memoized_per_instance_not_shared(fake_registry):
    a = _build_unit("ModelA")
    b = _build_unit("ModelB")

    assert a._resolve_model_class() is _ModelA
    assert b._resolve_model_class() is _ModelB
    # Calling again must return the same, still-correct class from the cache.
    assert a._resolve_model_class() is _ModelA


def test_a_run_id_of_none_leaves_the_model_detached_from_any_run(fake_registry):
    """No run id means no run, and a model with no run logs no metrics.

    ``ModelFactory`` hangs the run id on the model instance, and that
    attribute is the only thing ``BaseModel.calculate_metrics`` consults
    before deciding whether to write anything: ``if not metrics or not
    self.run_id`` returns early. So a caller with no run -- a pipeline -- gets
    a model that computes nothing into the ``Metric`` table, during training
    or after it, without the caller having to intercept anything.

    This is the sole reason ``run_id`` is nullable rather than required.
    """
    ctx = ExecutionContext()
    ctx.put("x", {"train": None, "validation": None})
    ctx.put("y", {"train": None, "validation": None})
    ctx.put("n_labels", None)
    ctx.put_ref("task_name", "ATask")

    _build_unit("ModelA", run_id=None)(ctx)

    assert ctx.get("model").run_id is None


def test_a_real_run_id_is_attached_to_the_model(fake_registry):
    """The mirror of the above: a run's model has to be able to log."""
    ctx = ExecutionContext()
    ctx.put("x", {"train": None, "validation": None})
    ctx.put("y", {"train": None, "validation": None})
    ctx.put("n_labels", None)
    ctx.put_ref("task_name", "ATask")

    _build_unit("ModelA", run_id=17)(ctx)

    assert ctx.get("model").run_id == 17
