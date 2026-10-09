"""Tests for the per-epoch reporting hook on BaseModel.

The hook exists so an optimizer can watch a trial while it trains. It lives on
the base class rather than inside each model's epoch loop because every model
that trains in epochs already routes its per-epoch metrics through
`calculate_metrics` — five loops across five files that share no common ancestor
below `BaseModel`.

What matters here is that it fires for exactly one combination (validation
metrics, epoch level) and stays out of the way otherwise.
"""

import pytest

from DashAI.back.core.enums.metrics import LevelEnum, SplitEnum
from DashAI.back.models.base_model import BaseModel


class ModelStub(BaseModel):
    """The smallest thing `calculate_metrics` will run against."""

    def __init__(self) -> None:
        self.run_id = 1
        self.saved: "list[tuple]" = []
        for split in SplitEnum:
            setattr(self, f"{split.value}_metrics", [Accuracy])

    def save(self, filename): ...

    def load(self, filename): ...

    def train(self, x_train, y_train, x_validation=None, y_validation=None): ...

    def predict(self, x_data):
        return x_data

    def prepare_output(self, y_data, is_fit=False):
        return y_data

    def _save_metrics(self, split, level, results, log_index=None, **kwargs):
        self.saved.append((split, level, results))


class Accuracy:
    @staticmethod
    def score(y_true, y_pred):
        return 0.75


@pytest.fixture
def model():
    return ModelStub()


def test_the_hook_fires_for_validation_metrics_of_an_epoch(model) -> None:
    seen = []
    model._epoch_reporter = lambda results, step: seen.append((results, step))

    model.calculate_metrics(
        split=SplitEnum.VALIDATION,
        level=LevelEnum.EPOCH,
        log_index=3,
        x_data=[0],
        y_data=[0],
    )

    assert seen == [({"Accuracy": 0.75}, 3)]


@pytest.mark.parametrize(
    ("split", "level"),
    [
        (SplitEnum.TRAIN, LevelEnum.EPOCH),
        (SplitEnum.VALIDATION, LevelEnum.TRIAL),
        (SplitEnum.VALIDATION, LevelEnum.LAST),
        (SplitEnum.TEST, LevelEnum.LAST),
    ],
)
def test_the_hook_stays_quiet_for_everything_else(model, split, level) -> None:
    """Training metrics and end-of-trial summaries are not pruning signals."""
    seen = []
    model._epoch_reporter = lambda results, step: seen.append((results, step))

    model.calculate_metrics(split=split, level=level, x_data=[0], y_data=[0])

    assert seen == []


def test_without_a_reporter_nothing_changes(model) -> None:
    """The default. Models that no optimizer is watching must be unaffected."""
    model.calculate_metrics(
        split=SplitEnum.VALIDATION,
        level=LevelEnum.EPOCH,
        log_index=1,
        x_data=[0],
        y_data=[0],
    )

    assert model.saved == [(SplitEnum.VALIDATION, LevelEnum.EPOCH, {"Accuracy": 0.75})]


def test_metrics_are_persisted_before_the_hook_can_abort(model) -> None:
    """Optuna prunes by raising from the reporter.

    The epoch that triggered the stop still happened, so its metrics have to be
    in the database already when the exception travels up.
    """

    def prune(results, step):
        raise RuntimeError("pruned")

    model._epoch_reporter = prune

    with pytest.raises(RuntimeError):
        model.calculate_metrics(
            split=SplitEnum.VALIDATION,
            level=LevelEnum.EPOCH,
            log_index=1,
            x_data=[0],
            y_data=[0],
        )

    assert model.saved, "the epoch's metrics were lost when the trial was pruned"
