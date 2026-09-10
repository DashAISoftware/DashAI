"""Tests for EvaluateModelToArtifactUnit, and its agreement with its sibling.

The agreement test is the load-bearing one. Two ways to score the same model
that both pass their own tests and return different numbers is the exact
failure this repository has already had once, when a prediction endpoint kept
its own copy of the three steps a prediction takes.
"""

import pytest

from DashAI.back.core.enums.metrics import LevelEnum, SplitEnum
from DashAI.back.units.context import ExecutionContext, UnitContractError
from DashAI.back.units.evaluate_model_to_artifact_unit import (
    EvaluateModelToArtifactUnit,
)


class _Accuracy:
    @staticmethod
    def score(y_true, y_pred):
        return 0.75


class _AlwaysNaN:
    @staticmethod
    def score(y_true, y_pred):
        return float("nan")


class _Model:
    """A model with the runtime state ModelFactory would have attached."""

    def __init__(self, run_id=None, metrics=(_Accuracy,), with_data=True):
        self.run_id = run_id
        self.train_metrics = list(metrics)
        self.validation_metrics = list(metrics)
        self.test_metrics = list(metrics)
        splits = {"train": "x-train", "validation": "x-val", "test": "x-test"}
        self.x_data = splits if with_data else None
        self.y_data = splits if with_data else None
        self.saved = []

    def predict(self, x_data):
        return [0, 1]

    def prepare_output(self, y_data, is_fit=False):
        return [0, 1]

    # The two methods under test come from BaseModel; this stands in for it
    # closely enough to exercise the unit without training anything.
    compute_metrics = None  # replaced below

    # Declared because ``calculate_metrics`` reads it directly: it is a class
    # attribute of ``BaseModel``, so every real model has it, but this double
    # borrows the method instead of inheriting it.
    _epoch_reporter = None


def _model(**kwargs):
    """A ``_Model`` borrowing BaseModel's real compute_metrics/_save_metrics."""
    from DashAI.back.models.base_model import BaseModel

    model = _Model(**kwargs)
    model.compute_metrics = BaseModel.compute_metrics.__get__(model, _Model)
    return model


def test_the_metrics_are_published_per_split():
    ctx = ExecutionContext()
    ctx.put("model", _model())

    EvaluateModelToArtifactUnit(splits=["TRAIN", "TEST"])(ctx)

    assert ctx.require("metrics") == {
        "train": {"_Accuracy": 0.75},
        "test": {"_Accuracy": 0.75},
    }


def test_the_metrics_travel_as_plain_data():
    """A ref, not a cached object: what a caller records is plain numbers."""
    ctx = ExecutionContext()
    ctx.put("model", _model())

    EvaluateModelToArtifactUnit(splits=["TRAIN"])(ctx)

    assert ctx.origin("metrics") == "ref"


def test_a_model_with_no_run_is_still_evaluated():
    """The whole point: no Run row, and the numbers still come out.

    ``EvaluateModelUnit`` cannot do this. Its metric rows are keyed by a
    foreign key to ``run.id``, so with no run it has nowhere to write, and
    ``calculate_metrics`` returns without scoring anything.
    """
    ctx = ExecutionContext()
    ctx.put("model", _model(run_id=None))

    EvaluateModelToArtifactUnit(splits=["VALIDATION"])(ctx)

    assert ctx.require("metrics") == {"validation": {"_Accuracy": 0.75}}


def test_a_split_with_nothing_to_score_is_left_out():
    """Absent is not the same as scored zero metrics.

    An empty entry would claim the split was evaluated and produced no
    metrics, which is a different statement from there being no data for it.
    """
    ctx = ExecutionContext()
    ctx.put("model", _model(with_data=False))

    EvaluateModelToArtifactUnit(splits=["TRAIN", "TEST"])(ctx)

    assert ctx.require("metrics") == {}


def test_a_non_finite_score_is_dropped_but_the_split_is_still_reported():
    """A split whose every metric was non-finite was still evaluated."""
    ctx = ExecutionContext()
    ctx.put("model", _model(metrics=(_AlwaysNaN,)))

    EvaluateModelToArtifactUnit(splits=["TRAIN"])(ctx)

    assert ctx.require("metrics") == {"train": {}}


def test_the_unit_needs_a_model():
    with pytest.raises(UnitContractError, match="'model'"):
        EvaluateModelToArtifactUnit(splits=["TRAIN"])(ExecutionContext())


def test_the_two_evaluation_paths_agree_on_the_same_model_and_split(monkeypatch):
    """The numbers the artifact carries are the numbers a run would have logged.

    Both paths score through ``BaseModel.compute_metrics``, so this fixes that
    they cannot drift into two answers for the same model.
    """
    from DashAI.back.models.base_model import BaseModel

    logged = {}

    # ``**kwargs`` rather than the exact signature: the real ``_save_metrics``
    # grew ``fold_index`` and ``inner_fold_index`` with cross-validation, and a
    # double that has to be edited every time a persistence-only argument is
    # added fails for a reason that has nothing to do with what it checks.
    def _capture(self, split, level, results, log_index=None, **kwargs):
        logged[split.value] = results

    monkeypatch.setattr(BaseModel, "_save_metrics", _capture)

    # The run path: a model with a run id, going through calculate_metrics.
    with_run = _model(run_id=7)
    with_run._save_metrics = BaseModel._save_metrics.__get__(with_run, _Model)
    BaseModel.calculate_metrics.__get__(with_run, _Model)(
        split=SplitEnum.TEST, level=LevelEnum.LAST
    )

    # The artifact path: the same model, no run, through the unit.
    ctx = ExecutionContext()
    ctx.put("model", _model(run_id=None))
    EvaluateModelToArtifactUnit(splits=["TEST"])(ctx)

    assert logged["test"] == ctx.require("metrics")["test"]


def test_base_model_defines_compute_metrics_exactly_once():
    """A second definition would silently win, and nothing else would notice.

    Cross-validation arrived on ``develop`` with its own copy of the scoring
    body, added to ``BaseModel`` under this same name while this branch was
    extracting the original one. The two do not overlap textually, so git
    merges them without a conflict and Python keeps whichever comes last --
    changing what every caller of ``calculate_metrics`` computes, including the
    filter that drops non-finite scores.

    Parsed rather than introspected: ``getattr`` sees one attribute either way,
    which is exactly why the duplicate went unnoticed.
    """
    import ast
    import inspect

    from DashAI.back.models import base_model

    tree = ast.parse(inspect.getsource(base_model))
    model_class = next(
        node
        for node in tree.body
        if isinstance(node, ast.ClassDef) and node.name == "BaseModel"
    )
    definitions = [
        node.name
        for node in model_class.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == "compute_metrics"
    ]

    assert definitions == ["compute_metrics"]
