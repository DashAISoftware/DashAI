"""Tests for FitModelUnit's validation, independent of an actual training run."""

import pytest
from kink import di

from DashAI.back.job.base_job import JobError
from DashAI.back.optimizers.optuna_optimizer import OptunaOptimizer
from DashAI.back.units.context import ExecutionContext, UnitContractError
from DashAI.back.units.fit_model_unit import FitModelUnit

# Two trials over one hyperparameter: the shape create_plots expects,
# small enough that only the filenames are under test here.
_TRIALS = [
    {"params": {"C": 0.1}, "value": 0.5},
    {"params": {"C": 1.0}, "value": 0.9},
]
_GOAL_METRIC = {"name": "Accuracy", "metadata": {"maximize": True}}


def _unit(
    optimizer_name="OptunaOptimizer",
    goal_metric="Accuracy",
    run_id=None,
    artifact_prefix=None,
):
    # run_id and artifact_prefix are read straight from the config, with no
    # default: omitting one is a KeyError rather than a silently disabled
    # runtime-state assertion or a plot filename nobody chose.
    return FitModelUnit(
        optimizer={"component": optimizer_name, "params": {}},
        goal_metric=goal_metric,
        run_id=run_id,
        artifact_prefix=artifact_prefix,
    )


def test_validate_raises_when_called_before_build_model_unit_has_run():
    """Regression: a missing key must not read as "nothing to optimize".

    ``optimizable_parameters`` is only absent from the context when
    ``BuildModelUnit`` hasn't run yet — a call-order mistake, not a model with
    no optimizable parameters (that case has the key present but empty).
    Before this fix, ``validate`` used ``ctx.get`` and treated both the same,
    silently skipping the optimizer/goal-metric checks it exists to run.
    """
    ctx = ExecutionContext()

    with pytest.raises(UnitContractError, match="'optimizable_parameters'"):
        _unit().validate(ctx)


def test_validate_is_a_noop_when_there_are_genuinely_no_optimizable_parameters():
    ctx = ExecutionContext()
    ctx.put("optimizable_parameters", [])

    # Should not raise, and should not need the optimizer/goal_metric to
    # resolve in the registry.
    unit = _unit(optimizer_name="DoesNotExist", goal_metric="DoesNotExist")
    unit.validate(ctx)

    assert unit._optimizer is None
    assert unit._goal_metric is None


def test_the_optimizer_is_kept_on_the_unit_not_in_the_shared_context():
    """Regression: the optimizer is this unit's own state, not an output.

    It used to be written to the context by ``validate`` and read back by
    ``execute``, using the shared context as a scratchpad between one unit's
    own two phases. Two FitModelUnits in one context would overwrite each
    other's optimizer, and the second would silently run the first one's.
    """

    class _Optimizer:
        def __init__(self, **params):
            pass

    registry = {
        "AnOptimizer": {"class": _Optimizer},
        "Accuracy": {"class": object, "metadata": {"maximize": True}},
    }
    di["component_registry"] = registry
    try:
        ctx = ExecutionContext()
        ctx.put("optimizable_parameters", ["lr"])

        unit = _unit(optimizer_name="AnOptimizer")
        unit.validate(ctx)

        assert isinstance(unit._optimizer, _Optimizer)
        assert not ctx.has("optimizer")
        assert not ctx.has("goal_metric")
    finally:
        del di["component_registry"]


def test_the_plot_filenames_come_from_the_artifact_prefix_when_there_is_one():
    """A caller that is not a run names the plots itself.

    Two pipeline executions have no run id to tell them apart, so without a
    prefix both would write ``history_objective_plot_None.pickle`` into the
    shared runs directory and the second would overwrite the first.
    """
    optimizer = OptunaOptimizer()

    filenames, _ = optimizer.create_plots(
        _TRIALS,
        None,
        n_params=1,
        goal_metric=_GOAL_METRIC,
        artifact_prefix="pipeline-3-fit",
    )

    assert filenames == [
        "history_objective_plot_pipeline-3-fit.pickle",
        "slice_plot_pipeline-3-fit.pickle",
    ]


def test_without_an_artifact_prefix_the_filenames_still_come_from_the_run_id():
    """The default has to leave a real run's filenames exactly as they were."""
    optimizer = OptunaOptimizer()

    named_by_default, _ = optimizer.create_plots(
        _TRIALS, 42, n_params=1, goal_metric=_GOAL_METRIC
    )
    named_explicitly, _ = optimizer.create_plots(
        _TRIALS, 42, n_params=1, goal_metric=_GOAL_METRIC, artifact_prefix=None
    )

    assert named_by_default == [
        "history_objective_plot_42.pickle",
        "slice_plot_42.pickle",
    ]
    assert named_explicitly == named_by_default


class _Detached:
    """What an optimizer must never return: a model with no data attached."""

    x_data = None
    run_id = None


class _Attached:
    """What ModelFactory produces: the splits hang off the instance."""

    x_data = {"train": "x"}
    run_id = None


def test_a_model_detached_from_its_data_is_refused_even_with_no_run():
    """The guard used to key on run_id, which made it a no-op for a pipeline.

    A pipeline always has run_id None, so returning early on that skipped the
    check for the one caller with no other signal: it would finish with an
    empty metrics artifact instead of an error. What both callers need is that
    the model still carries what scoring reads, so that is what is checked.
    """
    with pytest.raises(JobError, match="detached from its data"):
        FitModelUnit._assert_model_keeps_its_runtime_state(_Detached())


def test_a_model_that_kept_its_data_passes_without_a_run():
    FitModelUnit._assert_model_keeps_its_runtime_state(_Attached())


# --------------------------------------------------------------------------- #
# What the fit is allowed to look at
# --------------------------------------------------------------------------- #


class _RecordingModel:
    """Records what was asked of it, and does nothing else."""

    def __init__(self):
        self.fits = []
        self.logged = []
        self.x_data = None
        self.y_data = None

    def train(self, x_train, y_train, x_validation=None, y_validation=None):
        self.fits.append(
            {"train": x_train, "validation": x_validation},
        )

    def predict(self, x_data):
        return f"predictions-for-{x_data}"

    def prepare_output(self, y_data, is_fit=False):
        return f"expected-from-{y_data}"

    def calculate_metrics(self, split, level, **kwargs):
        self.logged.append((split, level))


def _fit_context(model, x, y):
    ctx = ExecutionContext()
    ctx.put("model", model)
    ctx.put("x", x)
    ctx.put("y", y)
    ctx.put("optimizable_parameters", [])
    ctx.put("factory", object())
    ctx.put_ref("model_parameters", {})
    ctx.put("task", object())
    return ctx


_HOLDOUT = {"train": "x-train", "validation": "x-val", "test": "x-test"}
#: What a fold splitter's trailing entry looks like: the pooled rows and the
#: reserved ones, and no validation partition at all.
_POOLED = {"train": "x-pool", "test": "x-reserved"}


def test_an_ordinary_fit_hands_the_validation_partition_over():
    """Models use it to watch the fit and stop early, which holdout wants."""
    model = _RecordingModel()

    _unit()(_fit_context(model, _HOLDOUT, _HOLDOUT))

    assert model.fits == [{"train": "x-train", "validation": "x-val"}]


def test_a_fit_that_will_be_scored_on_validation_does_not_look_at_it():
    """A fold is scored on the rows it held back from its own training.

    Handing them to the fit would measure it on data it was allowed to watch,
    and nothing about that failure raises -- the score simply comes out better
    than the model deserves.
    """
    model = _RecordingModel()
    unit = _unit()
    unit.config["validation_during_fit"] = False

    unit(_fit_context(model, _HOLDOUT, _HOLDOUT))

    assert model.fits == [{"train": "x-train", "validation": None}]


def test_a_partition_set_without_a_validation_split_still_fits():
    """The trailing entry of a fold splitter has nothing to hand over.

    Reading ``x["validation"]`` unconditionally, as this unit used to, is a
    KeyError on the very partition set that fits the model which gets kept.
    """
    model = _RecordingModel()

    _unit()(_fit_context(model, _POOLED, _POOLED))

    assert model.fits == [{"train": "x-pool", "validation": None}]


def test_the_fit_points_the_model_at_the_data_it_is_being_fitted_on():
    """Built once, fitted many times: the data comes with the fit, not the build.

    The metric methods read these attributes off the instance to decide what
    they are scoring, so over folds they have to follow the iteration.
    """
    model = _RecordingModel()
    # Same partition names on both sides, as a splitter always produces, and
    # distinguishable values so the two cannot be confused for one another.
    y = {name: value.replace("x-", "y-") for name, value in _HOLDOUT.items()}

    _unit()(_fit_context(model, _HOLDOUT, y))

    assert model.x_data is _HOLDOUT
    assert model.y_data is y


# --------------------------------------------------------------------------- #
# The objective the search measures
# --------------------------------------------------------------------------- #


class _NamedMetric:
    """Scores by naming what it was given, so the arguments can be checked."""

    @staticmethod
    def score(expected, predictions):
        return f"{expected}|{predictions}"


def test_one_trial_is_a_fit_and_a_score_of_the_validation_partition():
    """What the optimizer measures, and where the numbers come from.

    The objective used to be the optimizer's own business: it fitted and scored
    inline, and the sixth argument of ``optimize`` was the task. Making it a
    callable the unit supplies is what lets the same search be reused over
    anything that can be fitted and scored.
    """
    model = _RecordingModel()

    score = _unit()._score_one_trial(model, _HOLDOUT, _HOLDOUT, _NamedMetric)

    assert model.fits == [{"train": "x-train", "validation": "x-val"}]
    assert score == "expected-from-x-val|predictions-for-x-val"


def test_one_trial_logs_the_metrics_of_that_trial():
    """Written by the objective, not by the optimizer.

    What counts as a scored partition is a property of the thing being fitted
    rather than of the search, so it is decided here. A partition with no
    metrics configured writes nothing, because ``calculate_metrics`` finds
    nothing to score and returns.
    """
    from DashAI.back.core.enums.metrics import LevelEnum, SplitEnum

    model = _RecordingModel()

    _unit()._score_one_trial(model, _HOLDOUT, _HOLDOUT, _NamedMetric)

    assert model.logged == [
        (SplitEnum.TRAIN, LevelEnum.TRIAL),
        (SplitEnum.VALIDATION, LevelEnum.TRIAL),
    ]


class _RecordingOptimizer:
    """Stands in for a real optimizer to watch what it is handed."""

    last_call = None

    def optimize(self, model, x, y, parameters, metric, strategy):
        type(self).last_call = {
            "model": model,
            "parameters": parameters,
            "metric": metric,
            "strategy": strategy,
        }
        # A real optimizer leaves the model fitted at the best point it found.
        strategy(model, x, y, _NamedMetric)

    def get_model(self):
        return type(self).last_call["model"]

    def get_best_params(self):
        return {}

    def get_trials_values(self):
        return []

    def create_plots(self, trials, run_id, n_params, goal_metric, artifact_prefix):
        return [], []


class _Factory:
    @staticmethod
    def update_parameters(old, best):
        return dict(old)


def test_the_search_is_handed_the_units_own_objective(tmp_path):
    """The wiring, pinned separately from what the objective computes.

    Passing the wrong sixth argument is silent until the optimizer calls it:
    the task used to sit in that position, and a task is not callable, so the
    mistake surfaced from inside a trial rather than from the call.
    """
    registry = {
        "RecordingOptimizer": {"class": _RecordingOptimizer},
        "Accuracy": {"class": _NamedMetric, "metadata": {"maximize": True}},
    }
    di["component_registry"] = registry
    # A search names the plots it produces after the run, so the runs directory
    # is a real dependency of this path even when the double produces none.
    di["config"] = {"RUNS_PATH": str(tmp_path)}
    try:
        model = _RecordingModel()
        ctx = _fit_context(model, _HOLDOUT, _HOLDOUT)
        ctx.put("optimizable_parameters", [("obj", "C", (0, 1), "number")])
        ctx.put("factory", _Factory)

        unit = _unit(optimizer_name="RecordingOptimizer")
        unit(ctx)

        assert _RecordingOptimizer.last_call["strategy"] == unit._score_one_trial
        assert model.fits == [{"train": "x-train", "validation": "x-val"}]
    finally:
        del di["component_registry"]
        del di["config"]
