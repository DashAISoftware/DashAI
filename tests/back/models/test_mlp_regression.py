"""The hyperparameters an optimizer suggests must reach the network built.

``MLPRegression`` kept its configuration twice: in ``self.params``, the dict of
construction kwargs, and as instance attributes, which is where both
``ModelFactory`` and the optimizers write. ``train`` read the dict, so every
trial of a search rebuilt the same network out of the construction-time values.
The search ran, the study reported a best trial, and the model that came out of
it had never been trained with the values that won.

Nothing failed while that was true, which is why it needed a test rather than a
type: a study with all-identical trials is indistinguishable from a study on a
flat objective unless you look at what was built.

The dataset is 120 rows of three features and the networks are a handful of
epochs wide on purpose. This asserts wiring, not accuracy, and it should not
cost CI a minute.
"""

import numpy as np
import pyarrow as pa
import pytest

from DashAI.back.dataloaders.classes.dashai_dataset import to_dashai_dataset
from DashAI.back.evaluation.holdout import HoldoutEvaluationStrategy
from DashAI.back.metrics.regression.mse import MSE
from DashAI.back.models.scikit_learn.mlp_regression import MLPRegression
from DashAI.back.optimizers.optuna_optimizer import OptunaOptimizer
from DashAI.back.types.value_types import Float

EPOCHS = 3
N_TRIALS = 4

#: The width is searched over an interval wide enough that four independent
#: draws landing on the same value is not a plausible accident.
HIDDEN_SIZE_SPACE = (2, 40)


def _holdout_evaluate(model, input_dataset, output_dataset, metric):
    """The real holdout evaluation path, on a strategy with no factory.

    ``evaluate`` reads which partitions its strategy scores, so it needs a real
    instance rather than None for self. Building one through ``__init__`` would
    need a ``ModelFactory`` this test does not have, and does not need: the
    only thing read off the instance is a class attribute.
    """
    strategy = HoldoutEvaluationStrategy.__new__(HoldoutEvaluationStrategy)
    return strategy.evaluate(model, input_dataset, output_dataset, metric)


@pytest.fixture(scope="module", name="regression_splits")
def fixture_regression_splits():
    """A small synthetic regression dataset, split train/validation/test."""
    import pandas as pd

    rng = np.random.default_rng(0)
    n = 120
    frame = pd.DataFrame(
        {
            "x0": rng.uniform(-2, 2, n),
            "x1": rng.uniform(-2, 2, n),
            "x2": rng.uniform(-2, 2, n),
        }
    ).astype("float64")
    target = pd.DataFrame(
        {"target": 3.0 * frame["x0"] - 2.0 * frame["x1"] + rng.normal(0, 0.2, n)}
    ).astype("float64")

    feature_types = {c: Float(arrow_type=pa.float64()) for c in frame.columns}
    target_types = {"target": Float(arrow_type=pa.float64())}

    def part(start, stop):
        return (
            to_dashai_dataset(frame.iloc[start:stop], types=feature_types),
            to_dashai_dataset(target.iloc[start:stop], types=target_types),
        )

    x_train, y_train = part(0, 80)
    x_validation, y_validation = part(80, 100)
    x_test, y_test = part(100, 120)

    return (
        {"train": x_train, "validation": x_validation, "test": x_test},
        {"train": y_train, "validation": y_validation, "test": y_test},
    )


def _model(**overrides):
    """An ``MLPRegression`` with the runtime state a strategy expects."""
    params = {"epochs": EPOCHS, "hidden_size": 8, "learning_rate": 0.01}
    params.update(overrides)
    model = MLPRegression(**params)
    model.run_id = 1
    model.x_data = None
    model.y_data = None
    model.train_metrics = None
    model.validation_metrics = None
    model.test_metrics = None
    return model


def _record_widths(model):
    """Record the hidden width of every network ``train`` actually builds.

    Reading ``model.hidden_size`` afterwards would prove nothing: the optimizer
    writes that attribute itself, so it holds the last suggested value whether
    or not ``train`` ever read it. What has to be observed is the network.
    """
    widths = []
    original = model.mlp

    def spy(input_dim, hidden_size, activation_name):
        widths.append(hidden_size)
        return original(input_dim, hidden_size, activation_name)

    model.mlp = spy
    return widths


def test_suggested_values_reach_training(regression_splits):
    """Every trial must train the width Optuna suggested for it.

    This is the assertion that fails on the unfixed model: the widths built are
    ``[8, 8, 8, 8]`` -- the construction-time value -- while the study reports
    four different suggestions.
    """
    x, y = regression_splits
    model = _model()
    widths = _record_widths(model)

    optimizer = OptunaOptimizer(
        n_trials=N_TRIALS, sampler="RandomSampler", pruner="None"
    )
    optimizer.optimize(
        model,
        x,
        y,
        [(model, "hidden_size", HIDDEN_SIZE_SPACE, "integer")],
        {"class": MSE, "metadata": {"maximize": False}},
        _holdout_evaluate,
    )

    suggested = [trial.params["hidden_size"] for trial in optimizer.study.trials]
    assert widths == suggested, (
        f"the networks trained were {widths} wide, but Optuna suggested "
        f"{suggested}. A width the search never chose means the trial scored a "
        "model built from the construction-time configuration, so the study's "
        "best trial describes a model that was never trained."
    )


def test_a_written_attribute_reaches_training(regression_splits):
    """The same guarantee without Optuna, as the cheap negative control.

    ``ModelFactory`` and both optimizers configure a model the same way: plain
    ``setattr`` on the instance. If this ever passes while the test above fails,
    the break is in the optimizer, not in the model.
    """
    x, y = regression_splits
    model = _model(hidden_size=8)
    widths = _record_widths(model)

    model.hidden_size = 23
    model.train(x["train"], y["train"])

    assert widths == [23], (
        f"training built a network {widths} wide after the width was set to 23"
    )


def test_defaults_match_the_declared_schema():
    """The fallbacks must be the values the schema declares, all of them.

    ``hidden_size`` used to fall back to 100 when training and to 5 when
    reloading, against a schema that declares 16: three answers to one
    question, and a checkpoint saved without that key came back as a different
    network. Pinning the table to the schema is what stops them drifting apart
    again, and it also fails when a field is added to the schema and forgotten
    here.
    """
    properties = MLPRegression.get_schema()["properties"]

    # ``device`` is resolved into a torch device string by ``__init__`` rather
    # than mirrored, so it is the one field that is not in the table.
    assert set(MLPRegression._CONFIG_DEFAULTS) == set(properties) - {"device"}, (
        "the defaults table and the schema disagree about which fields exist"
    )

    for name, default in MLPRegression._CONFIG_DEFAULTS.items():
        placeholder = properties[name]["placeholder"]
        # A search space declares its default inside the optimize envelope.
        declared = (
            placeholder["fixed_value"]
            if isinstance(placeholder, dict) and "fixed_value" in placeholder
            else placeholder
        )
        assert default == declared, (
            f"'{name}' falls back to {default!r} but the schema declares {declared!r}"
        )


def test_the_schema_defaults_are_what_an_unconfigured_model_uses():
    """And the table is what the attributes are actually built from."""
    model = MLPRegression()
    for name, default in MLPRegression._CONFIG_DEFAULTS.items():
        assert getattr(model, name) == default, f"'{name}' was not mirrored"


def test_checkpoint_records_the_configuration_that_was_trained(
    regression_splits, tmp_path
):
    """A checkpoint must describe the network it holds the weights of.

    ``save`` wrote the construction kwargs, so a model saved after a search
    stored the pre-search width beside post-search weights. Reloading it
    rebuilt a network of the wrong width, which surfaces as a shape mismatch
    inside ``load_state_dict`` -- an error that names a tensor, not the reason.
    """
    x, y = regression_splits
    model = _model(hidden_size=8)

    # What the optimizer does to a model between construction and training.
    model.hidden_size = 19
    model.train(x["train"], y["train"])

    path = tmp_path / "mlp.pt"
    model.save(str(path))
    restored = MLPRegression.load(str(path))

    assert restored.hidden_size == 19
    assert restored.model.model[0].out_features == 19

    original = model.predict(x["test"])
    assert np.allclose(original, restored.predict(x["test"]), atol=1e-6), (
        "the reloaded model does not reproduce the predictions of the saved one"
    )
