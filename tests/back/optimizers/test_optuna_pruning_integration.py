"""End-to-end proof that a trial actually gets pruned.

The unit tests cover each piece: the reporter reports, the hook fires only for
epoch+validation, `TrialPruned` is raised. This one wires the real parts
together and checks the outcome Optuna records, which is what the feature is
for — a pruner that never prunes passes every unit test in the file next door.

Real, not stubbed: `OptunaOptimizer.optimize`, `HoldoutEvaluationStrategy.
evaluate` (the strategy that trains with validation data), `BaseModel.
calculate_metrics` (where the hook lives), `_report_epoch`, and Optuna's own
MedianPruner and trial bookkeeping.

Stubbed: `_save_metrics` (persistence needs a database and is not what this
proves) and the training itself, which is replaced by a loop that improves by a
fixed amount per epoch. The loop calls `calculate_metrics` exactly as the five
models that train in epochs do — same split, same level, same log_index.

Which trials get pruned is decided by trial order, not by the value the sampler
draws. Tying it to the draw made these tests fail about one run in twenty — the
runs where no trial happened to land below the median. A test for pruning that
only usually prunes reports the pruner as broken at random, which is worse than
not having it.
"""

import optuna
import pytest

from DashAI.back.core.enums.metrics import LevelEnum, SplitEnum
from DashAI.back.evaluation.holdout import HoldoutEvaluationStrategy
from DashAI.back.models.base_model import BaseModel
from DashAI.back.optimizers.optuna_optimizer import OptunaOptimizer


def _holdout_evaluate(model, input_dataset, output_dataset, metric):
    """The real holdout evaluation path, on a strategy with no factory.

    `evaluate` reads which partitions its strategy scores, so it needs a real
    instance rather than None for self. Building one through __init__ would
    need a `ModelFactory` this test does not have, and does not need: the only
    thing read off the instance is a class attribute.
    """
    strategy = HoldoutEvaluationStrategy.__new__(HoldoutEvaluationStrategy)
    return strategy.evaluate(model, input_dataset, output_dataset, metric)


EPOCHS = 12
N_TRIALS = 10
# MedianPruner never prunes its first `n_startup_trials` (5 by default): with
# nothing to compare against there is no median. Every trial after those is
# below it by construction here, so the split is exact.
STARTUP_TRIALS = 5


class Score:
    """Metric class. Named because results are keyed by `metric.__name__`."""

    @staticmethod
    def score(y_true, y_pred):
        return y_pred


class SteppedModel(BaseModel):
    """A model that gets worse every trial, revealing it epoch by epoch.

    Each trial improves by `1 / (1 + trials already run)` per epoch, so trial 5
    onwards is below the median of everything before it from its first epoch —
    exactly the situation a pruner exists to cut short, and one that does not
    depend on chance.

    `rate` is still declared as the optimizable parameter so the optimizer's
    own path runs for real; it just does not decide the outcome under test.
    """

    def __init__(self):
        self.run_id = 1
        self.rate = 1.0
        self.value = 0.0
        self.epochs_run = 0
        self.trials_run = 0
        for split in SplitEnum:
            setattr(self, f"{split.value}_metrics", [Score])
        # The optimizer also asks for trial-level metrics without passing data,
        # so `calculate_metrics` falls back to what the model holds.
        self.x_data = {split.value: [0] for split in SplitEnum}
        self.y_data = {split.value: [0] for split in SplitEnum}

    def save(self, filename): ...

    def load(self, filename): ...

    def train(self, x_train, y_train, x_validation=None, y_validation=None):
        self.value = 0.0
        quality = 1.0 / (1.0 + self.trials_run)
        self.trials_run += 1
        for epoch in range(EPOCHS):
            self.value += quality
            self.epochs_run += 1
            # Same call the real epoch loops make.
            self.calculate_metrics(
                split=SplitEnum.VALIDATION,
                level=LevelEnum.EPOCH,
                x_data=[0],
                y_data=[0],
                log_index=epoch + 1,
            )

    def predict(self, x_data):
        return self.value

    def prepare_output(self, y_data, is_fit=False):
        return y_data

    def _save_metrics(self, split, level, results, log_index=None, **kwargs):
        """Persistence is out of scope; the database is not what this proves."""


@pytest.fixture
def dataset():
    return {"train": [0], "validation": [0]}


def _run(pruner, n_trials=N_TRIALS):
    model = SteppedModel()
    optimizer = OptunaOptimizer(
        n_trials=n_trials, sampler="RandomSampler", pruner=pruner
    )
    optimizer.optimize(
        model,
        dataset := {"train": [0], "validation": [0]},
        dataset,
        [(model, "rate", (0.01, 10.0), "number")],
        {"class": Score, "metadata": {"maximize": True}},
        _holdout_evaluate,
    )
    return optimizer, model


def _states(optimizer):
    return [t.state for t in optimizer.study.trials]


def test_a_bad_trial_is_actually_pruned():
    """The outcome that matters: Optuna records trials as PRUNED."""
    optimizer, _ = _run("MedianPruner")

    pruned = [s for s in _states(optimizer) if s is optuna.trial.TrialState.PRUNED]

    assert len(pruned) == N_TRIALS - STARTUP_TRIALS, (
        f"{len(pruned)} trials were pruned, expected exactly "
        f"{N_TRIALS - STARTUP_TRIALS}. None at all means the pruner is inert: "
        "either the epoch metrics never reach the trial, or TrialPruned is being "
        "swallowed before Optuna sees it."
    )


def test_pruning_stops_training_early():
    """A pruned trial must cost fewer epochs than a completed one.

    Pruning that reports the right verdict but keeps training saves nothing,
    which is the whole point of early stopping.
    """
    _, with_pruning = _run("MedianPruner")
    _, without = _run("NopPruner")

    # Pruned trials die on their first epoch: their opening score is already
    # below the median. No refit here: `optimize` only writes the best params
    # back, and the final training happens later in the strategy's `execute`.
    expected = STARTUP_TRIALS * EPOCHS + (N_TRIALS - STARTUP_TRIALS)

    assert without.epochs_run == N_TRIALS * EPOCHS
    assert with_pruning.epochs_run == expected, (
        f"pruning ran {with_pruning.epochs_run} epochs, expected {expected}. "
        f"Reaching {without.epochs_run} means the trials were cut short on paper "
        "only and training kept going."
    )


def test_disabled_pruning_completes_every_trial():
    """The control.

    With pruning off nothing may be cut, or the test above proves nothing.
    """
    optimizer, model = _run("NopPruner")

    states = _states(optimizer)
    assert all(s is optuna.trial.TrialState.COMPLETE for s in states)
    assert len(states) == N_TRIALS
    # No refit inside `optimize`: final training belongs to the strategy.
    assert model.epochs_run == EPOCHS * N_TRIALS
