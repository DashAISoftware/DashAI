"""Contract tests for the unit that fits a model across folds.

Built on a hand-made ``ExecutionContext`` rather than through a job. The
end-to-end net already runs this unit inside a real run; what it cannot show is
what the unit reads, promises and refuses on its own, which is where the
composability mistakes live.
"""

import pytest
from kink import di

from DashAI.back.core.enums.metrics import LevelEnum, SplitEnum
from DashAI.back.units.context import ExecutionContext, UnitContractError
from DashAI.back.units.fit_model_over_folds_unit import FitModelOverFoldsUnit

#: Three folds and the trailing entry, which is not one: it holds every row the
#: folds could use and the rows reserved from them.
FOLDS = [
    {"train": "train-0", "validation": "val-0"},
    {"train": "train-1", "validation": "val-1"},
    {"train": "train-2", "validation": "val-2"},
    {"train": "pool", "test": "reserved"},
]


class _RecordingModel:
    """Records what was asked of it, and scores by naming what it saw."""

    def __init__(self, run_id=7, metrics=("Accuracy",)):
        self.run_id = run_id
        self._metrics = list(metrics)
        self.fits = []
        self.logged = []
        self.saved = []
        self.x_data = None
        self.y_data = None
        self._score = 0.0

    def train(self, x_train, y_train, x_validation=None, y_validation=None):
        self.fits.append({"train": x_train, "validation": x_validation})

    def predict(self, x_data):
        return f"predictions-for-{x_data}"

    def prepare_output(self, y_data, is_fit=False):
        return f"expected-from-{y_data}"

    def compute_metrics(self, split, x_data=None, y_data=None):
        if not self._metrics:
            return None
        # A different number every time, so a mean over folds is not the same
        # as any one of them.
        self._score += 1.0
        return dict.fromkeys(self._metrics, self._score)

    def calculate_metrics(self, split, level, fold_index=None, **kwargs):
        if not self.run_id:
            return None
        results = self.compute_metrics(split)
        if results is None:
            return None
        self.logged.append((split, level, fold_index))
        return results

    def _save_metrics(self, results, split, level, **kwargs):
        self.saved.append((split, level, results))


class _Metric:
    """Scores by naming what it was given."""

    __name__ = "Accuracy"

    @staticmethod
    def score(expected, predictions):
        return 1.0


class _Factory:
    @staticmethod
    def update_parameters(old, best):
        return dict(old)


def _unit(**overrides):
    config = {
        "optimizer": {"component": "AnOptimizer", "params": {}},
        "goal_metric": "Accuracy",
        "run_id": 7,
        "artifact_prefix": "7",
    }
    config.update(overrides)
    return FitModelOverFoldsUnit(**config)


def _context(model, folds=None):
    ctx = ExecutionContext()
    ctx.put("model", model)
    ctx.put("x_folds", folds if folds is not None else FOLDS)
    ctx.put("y_folds", folds if folds is not None else FOLDS)
    ctx.put("optimizable_parameters", [])
    ctx.put("factory", _Factory)
    ctx.put_ref("model_parameters", {})
    return ctx


# --------------------------------------------------------------------------- #
# The fold loop
# --------------------------------------------------------------------------- #


def test_every_fold_is_fitted_and_the_kept_model_once_more():
    """Three folds and a refit, and the refit is on the pooled rows."""
    model = _RecordingModel()

    _unit()(_context(model))

    assert [fit["train"] for fit in model.fits] == [
        "train-0",
        "train-1",
        "train-2",
        "pool",
    ]


def test_the_trailing_entry_is_never_scored_as_a_fold():
    """It is not a fold: it fits the model that gets kept.

    Scoring it as one would put the pooled rows -- which every fold trained on
    -- into the mean that is meant to describe how the model does on rows it
    has not seen.
    """
    model = _RecordingModel()

    _unit()(_context(model))

    fold_indexes = sorted(
        {index for _, level, index in model.logged if index is not None}
    )
    assert fold_indexes == [0, 1, 2]


def test_no_fold_fit_receives_validation_data():
    """A fold is scored on the rows it held back, so the fit may not see them.

    Nothing raises when it does; the score simply comes out better than the
    model deserves. Unlike the holdout sibling this is not configurable,
    because there is no reading of a fold under which it would be right.
    """
    model = _RecordingModel()

    _unit()(_context(model))

    assert all(fit["validation"] is None for fit in model.fits)


def test_the_fold_rows_are_written_at_the_fold_level_and_indexed_from_zero():
    """Contiguous from zero, which the repeated-cross-validation charts assume.

    They bucket folds into repetitions by integer division, so a gap moves a
    fold into the wrong repetition rather than raising.
    """
    model = _RecordingModel()

    _unit()(_context(model))

    by_split = {}
    for split, level, index in model.logged:
        assert level is LevelEnum.FOLD
        by_split.setdefault(split, []).append(index)

    assert set(by_split) == {SplitEnum.TRAIN, SplitEnum.VALIDATION}
    for split, indexes in by_split.items():
        assert indexes == [0, 1, 2], split


def test_the_per_fold_scores_are_published_for_whoever_aggregates_them():
    """The unit does not summarise them itself.

    A summary row carries a standard deviation, and the one sanctioned write in
    the domain layer has nowhere to put one -- so the numbers are handed over
    and the caller persists the summary.
    """
    model = _RecordingModel()
    ctx = _context(model)

    _unit()(ctx)

    fold_metrics = ctx.require("fold_metrics")
    assert set(fold_metrics) == {"TRAIN", "VALIDATION"}
    for split_name, by_metric in fold_metrics.items():
        assert set(by_metric) == {"Accuracy"}, split_name
        assert len(by_metric["Accuracy"]) == 3, split_name


def test_the_model_ends_pointing_at_the_partitions_it_was_last_fitted_on():
    """Whatever scores it afterwards reads the data off the instance."""
    model = _RecordingModel()

    _unit()(_context(model))

    assert model.x_data is FOLDS[-1]
    assert model.y_data is FOLDS[-1]


def test_a_split_with_no_metrics_configured_is_absent_rather_than_empty():
    """Present and empty would claim it was scored and produced nothing."""
    model = _RecordingModel(metrics=())
    ctx = _context(model)

    _unit()(ctx)

    assert ctx.require("fold_metrics") == {}


# --------------------------------------------------------------------------- #
# The objective the search measures
# --------------------------------------------------------------------------- #


def test_one_trial_fits_every_fold_and_returns_their_mean():
    """A trial costs k fits. That is what cross-validation buys, and its price."""
    model = _RecordingModel()

    score = _unit()._score_one_trial(model, FOLDS, FOLDS, _Metric)

    assert [fit["train"] for fit in model.fits] == ["train-0", "train-1", "train-2"]
    assert score == 1.0


def test_one_trial_records_one_row_per_split_holding_the_mean_of_its_folds():
    """Not one row per fold: those measure a setting, not the kept model."""
    model = _RecordingModel()

    _unit()._score_one_trial(model, FOLDS, FOLDS, _Metric)

    assert [(split, level) for split, level, _ in model.saved] == [
        (SplitEnum.TRAIN, LevelEnum.TRIAL),
        (SplitEnum.VALIDATION, LevelEnum.TRIAL),
    ]
    # Three folds scoring 1, 3, 5 on TRAIN (the double counts every call) means
    # the row is their mean and not any one of them.
    train_row = model.saved[0][2]
    assert train_row["Accuracy"] == 3.0


def test_a_trial_writes_no_rows_when_there_is_no_run_to_write_against():
    """``_save_metrics`` does not guard this for itself.

    A caller with no run -- a pipeline -- would write rows against a foreign
    key pointing at nothing, and they insert without complaint because nothing
    enforces it. That is the failure a metrics unit already exists to refuse.
    """
    model = _RecordingModel(run_id=None)

    _unit()._score_one_trial(model, FOLDS, FOLDS, _Metric)

    assert model.saved == []
    assert model.fits, "the folds are still fitted; only the recording is refused"


# --------------------------------------------------------------------------- #
# The contract itself
# --------------------------------------------------------------------------- #


def test_the_unit_refuses_to_run_before_the_model_was_built():
    """``__call__`` checks REQUIRES, so the failure names the missing key."""
    with pytest.raises(UnitContractError):
        _unit()(ExecutionContext())


def test_validate_raises_when_called_before_the_model_was_built():
    """A missing key is a call-order mistake, not "nothing to optimize".

    The two are different: the key present and empty is a model that declares
    no optimizable parameters, and that one legitimately skips the checks.
    """
    with pytest.raises(UnitContractError, match="'optimizable_parameters'"):
        _unit().validate(ExecutionContext())


def test_two_units_in_one_context_do_not_share_their_optimizer():
    """Instance state stays on the instance, which is what lets a graph hold two.

    A context-global cache would give the second unit the first one's
    optimizer, and the second search would silently run the first one's.
    """

    class _Optimizer:
        def __init__(self, **params):
            pass

    registry = {
        "AnOptimizer": {"class": _Optimizer},
        "Accuracy": {"class": _Metric, "metadata": {"maximize": True}},
    }
    di["component_registry"] = registry
    try:
        ctx = ExecutionContext()
        ctx.put("optimizable_parameters", ["lr"])

        first, second = _unit(), _unit()
        first.validate(ctx)
        second.validate(ctx)

        assert first._optimizer is not second._optimizer
        assert not ctx.has("optimizer")
    finally:
        del di["component_registry"]
