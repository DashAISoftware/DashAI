"""OptunaOptimizer must retrain the BEST trial's model, not the last one.

`ModelFactory` hands the optimizer a list of ``(owner, key, bounds, dtype)``
tuples where ``owner`` is the object that actually declares the parameter, which
for a composite model is a nested sub-component rather than the top-level model.
Writing the best values onto the wrapper leaves the sub-component holding the
last trial's value, so the model that is retrained and serialized is not the one
the study selected.
"""

import pytest

from DashAI.back.core.enums.metrics import LevelEnum, SplitEnum
from DashAI.back.optimizers.optuna_optimizer import OptunaOptimizer

TARGET = 5.0
BOUNDS = (0.01, 10.0)


class DummySubComponent:
    """Stands in for a nested component such as the SVC inside a bag-of-words model."""

    def __init__(self):
        self.C = 1.0


class DummyModel:
    """Minimal model whose prediction depends only on the sub-component."""

    def __init__(self):
        self.sub = DummySubComponent()
        self.trained_with = None

    def train(self, x, y, x_validation=None, y_validation=None):
        # Record what the model was actually fitted with, which is the value the
        # sub-component holds at that moment.
        self.trained_with = self.sub.C

    def predict(self, dataset):
        return self.sub.C

    def calculate_metrics(self, split=None, level=None):
        assert split in (SplitEnum.TRAIN, SplitEnum.VALIDATION)
        assert level is LevelEnum.TRIAL

    def prepare_output(self, dataset, is_fit=False):
        return dataset


class DummyMetric:
    """Score peaks at C == TARGET, so the best trial is whichever lands closest."""

    @staticmethod
    def score(y_true, y_pred):
        return -abs(y_pred - TARGET)


@pytest.fixture
def dataset():
    return {"train": [0], "validation": [0]}


def _optimize(model, parameters, dataset, n_trials=12):
    optimizer = OptunaOptimizer(n_trials=n_trials, sampler="RandomSampler", pruner=None)

    # Define the strategy function that will be used to evaluate the model
    # during optimization
    def strategy(model, input_dataset, output_dataset, metric):
        model.train(input_dataset["train"], output_dataset["train"])
        y_pred = model.predict(input_dataset["validation"])
        output_dataset_transformed = model.prepare_output(
            output_dataset["validation"], is_fit=False
        )
        score = metric.score(output_dataset_transformed, y_pred)
        return score

    optimizer.optimize(
        model,
        dataset,
        dataset,
        parameters,
        {"class": DummyMetric, "metadata": {"maximize": True}},
        strategy,
    )
    optimizer.model.train(dataset["train"], dataset["train"])
    return optimizer


def test_nested_component_keeps_best_params_not_last_trial(dataset):
    """The nested sub-component must end up holding the study's best value."""
    model = DummyModel()
    # The owner is the sub-component, exactly as ModelFactory would report it.
    parameters = [(model.sub, "C", BOUNDS, "number")]

    optimizer = _optimize(model, parameters, dataset)
    best = optimizer.get_best_params()["C"]

    assert pytest.approx(best) == model.sub.C, (
        "the sub-component kept a value that is not the best one found; "
        "the best params were written onto the wrapper instead of the owner"
    )
    assert model.trained_with == pytest.approx(best), (
        "the final retrain used a value other than the best one"
    )


def test_nested_component_ignores_wrapper_attribute(dataset):
    """Writing onto the wrapper is inert: nothing reads a `C` set on the parent."""
    model = DummyModel()
    parameters = [(model.sub, "C", BOUNDS, "number")]

    optimizer = _optimize(model, parameters, dataset)
    best = optimizer.get_best_params()["C"]

    # `predict` and `train` only ever look at `model.sub.C`. If the fix regressed
    # and the value went to the wrapper, `model.sub.C` would hold the last trial's
    # value and this comparison would fail.
    assert pytest.approx(best) == model.sub.C
    assert getattr(model, "C", None) is None, (
        "the optimizer set an attribute on the wrapper that nothing reads"
    )


def test_flat_model_still_works(dataset):
    """On a flat model the owner IS the model, and behaviour must not change."""

    class FlatModel(DummyModel):
        def __init__(self):
            super().__init__()
            self.C = 1.0

        def train(self, x, y, x_validation=None, y_validation=None):
            self.trained_with = self.C

        def predict(self, dataset):
            return self.C

    model = FlatModel()
    parameters = [(model, "C", BOUNDS, "number")]

    optimizer = _optimize(model, parameters, dataset)
    best = optimizer.get_best_params()["C"]

    assert pytest.approx(best) == model.C
    assert model.trained_with == pytest.approx(best)


def test_integer_parameters_keep_their_type(dataset):
    """Integer hyperparameters must survive as ints on the owner."""

    class IntSub:
        def __init__(self):
            self.n = 1

    class IntModel(DummyModel):
        def __init__(self):
            super().__init__()
            self.sub = IntSub()

        def train(self, x, y, x_validation=None, y_validation=None):
            self.trained_with = self.sub.n

        def predict(self, dataset):
            return float(self.sub.n)

    model = IntModel()
    parameters = [(model.sub, "n", (1, 10), "integer")]

    optimizer = _optimize(model, parameters, dataset)
    best = optimizer.get_best_params()["n"]

    assert model.sub.n == best
    assert isinstance(model.sub.n, int)
