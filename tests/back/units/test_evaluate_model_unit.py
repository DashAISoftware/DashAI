"""Tests for EvaluateModelUnit's contract, independent of a real database."""

import pytest

from DashAI.back.job.base_job import JobError
from DashAI.back.units.context import ExecutionContext, UnitContractError
from DashAI.back.units.evaluate_model_unit import EvaluateModelUnit


def test_call_refuses_to_run_without_a_run_id():
    """Regression: a missing run id must fail loudly, not silently no-op.

    The idempotency check filters an existing-metric query by ``run_id``; a
    ``None`` value would match no row regardless of what was already logged,
    and -- if the model were also detached from its run --
    ``BaseModel.calculate_metrics`` no-ops on a falsy ``run_id`` too. Either
    way the unit could "succeed" having written zero metrics instead of
    surfacing the missing wiring.

    The run id is configuration rather than a context key (no unit publishes
    it), so the guard lives in ``validate`` instead of in ``REQUIRES``.
    """
    ctx = ExecutionContext()
    ctx.put("model", object())

    with pytest.raises(JobError, match="no run id"):
        EvaluateModelUnit(run_id=None)(ctx)


def test_validate_refuses_a_missing_run_id_before_any_metric_is_computed():
    """``__call__`` validates first, so nothing is written on the way out."""
    with pytest.raises(JobError, match="no run id"):
        EvaluateModelUnit(run_id=None).validate(ExecutionContext())


def test_the_unit_still_needs_a_model():
    """``run_id`` left REQUIRES; ``model`` did not."""
    with pytest.raises(UnitContractError, match="'model'"):
        EvaluateModelUnit(run_id=1)(ExecutionContext())
