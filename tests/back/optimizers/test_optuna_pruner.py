"""Tests for pruner resolution in OptunaOptimizer.

Regression coverage for the pruner being passed to ``optuna.create_study`` as a
raw schema string instead of a pruner instance. ``create_study`` does not
validate the argument, so the study was built with ``pruner`` set to a ``str``
and any pruning call raised ``AttributeError: 'str' object has no attribute
'prune'``.
"""

import optuna
import pytest

from DashAI.back.optimizers.optuna_optimizer import _build_pruner, _report_epoch


@pytest.mark.parametrize(
    "name",
    ["MedianPruner", "HyperbandPruner", "SuccessiveHalvingPruner", "WilcoxonPruner"],
)
def test_build_pruner_returns_an_instance(name: str) -> None:
    pruner = _build_pruner(name)

    assert isinstance(pruner, optuna.pruners.BasePruner)
    assert type(pruner).__name__ == name


@pytest.mark.parametrize("disabled", [None, "", "None"])
def test_disabled_pruning_maps_to_nop_pruner(disabled: "str | None") -> None:
    """The schema sends the string "None" when the user disables pruning."""
    assert isinstance(_build_pruner(disabled), optuna.pruners.NopPruner)


def test_pruner_needing_configuration_fails_with_a_clear_message() -> None:
    """PatientPruner wraps another pruner, so it cannot be built from its name."""
    with pytest.raises(ValueError, match="requires configuration"):
        _build_pruner("PatientPruner")


def test_unknown_pruner_lists_the_valid_options() -> None:
    with pytest.raises(ValueError, match="Unknown pruner 'NotAPruner'") as excinfo:
        _build_pruner("NotAPruner")

    assert "MedianPruner" in str(excinfo.value)


def test_study_built_with_the_resolved_pruner_can_prune() -> None:
    """End to end: the failure mode this fixes was only visible when pruning."""
    study = optuna.create_study(
        direction="maximize", pruner=_build_pruner("MedianPruner")
    )
    trial = study.ask()
    trial.report(0.1, step=0)

    # With the raw string this raised AttributeError instead of returning a bool.
    assert trial.should_prune() in (True, False)


# --- Reporting each epoch to the trial -------------------------------------
#
# Resolving the pruner is not enough on its own: a pruner only ever acts if the
# trial is told how it is doing while it still runs. These cover that half.


class _Trial:
    """Records what a trial was told, and answers should_prune() on cue."""

    def __init__(self, prune_at: "int | None" = None) -> None:
        self.reported: "list[tuple[float, int]]" = []
        self.prune_at = prune_at

    def report(self, value: float, step: int) -> None:
        self.reported.append((value, step))

    def should_prune(self) -> bool:
        return self.prune_at is not None and len(self.reported) >= self.prune_at


class Accuracy:
    """Stands in for a dashAI metric class.

    Only its name matters: `calculate_metrics` keys its results by
    ``metric.__name__``, so that is what the reporter looks up. Assigning
    ``__name__`` inside a class body does NOT rename the class — ``type.__name__``
    is a data descriptor and wins — so the double has to actually be named after
    the metric.
    """


def test_each_epoch_is_reported_with_its_step() -> None:
    trial = _Trial()

    report = _report_epoch(trial, Accuracy)
    report({"Accuracy": 0.4}, 1)
    report({"Accuracy": 0.6}, 2)

    assert trial.reported == [(0.4, 1), (0.6, 2)]


def test_a_trial_the_pruner_rejects_raises_trial_pruned() -> None:
    """`TrialPruned` is how Optuna is told to abandon a trial.

    It has to travel from inside the model's epoch loop up to `study.optimize`,
    so nothing in between may swallow it.
    """
    trial = _Trial(prune_at=1)

    report = _report_epoch(trial, Accuracy)
    with pytest.raises(optuna.TrialPruned):
        report({"Accuracy": 0.1}, 1)


def test_a_metric_missing_from_the_epoch_is_not_an_error() -> None:
    """`calculate_metrics` drops metrics that return a non-finite value.

    An epoch with only one class present in the split is a real case, so the
    optimized metric can legitimately be absent. That trial keeps running.
    """
    trial = _Trial(prune_at=1)

    report = _report_epoch(trial, Accuracy)
    report({"F1": 0.9}, 1)

    assert trial.reported == []


def test_the_reported_metric_is_the_one_being_optimized() -> None:
    trial = _Trial()

    report = _report_epoch(trial, Accuracy)
    report({"F1": 0.1, "Accuracy": 0.9, "Precision": 0.5}, 1)

    assert trial.reported == [(0.9, 1)]
