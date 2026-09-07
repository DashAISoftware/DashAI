"""Searching a parameter that is chosen out of a set rather than measured.

HPO worked for integers and floats only, and not by accident: the envelope the
form sends carries ``lower_bound`` and ``upper_bound``, and that vocabulary can
only describe a scale. ``hinge`` is not between ``squared_hinge`` and anything
else, so there was nothing for a user to fill in, and both optimizers branched
on a dtype that could only ever be ``"number"`` or ``"integer"``.

Of the 204 fields in the 31 models that already do numeric search, 38 are enums
and 18 are booleans. A boolean is the same situation as an enum with two
options, so one mechanism covers all 56.

Each optimizer had its own way of not supporting this:

* Optuna raised ``ValueError`` for any other dtype, which is the honest
  failure.
* Hyperopt's space builder was an ``if``/``elif`` with no ``else``, so the
  parameter was left out of the space entirely and silently never optimized.
* Hyperopt reports the *index* of the chosen option, not the option, in
  everything it hands back after ``fmin``. The old code read that through
  ``float(raw_value)``, which would have set ``loss = 1.0`` on the final model.
"""

import pytest

from DashAI.back.core.enums.metrics import LevelEnum, SplitEnum
from DashAI.back.models.model_factory import _search_space_of
from DashAI.back.optimizers.hyperopt_optimizer import HyperOptOptimizer
from DashAI.back.optimizers.optuna_optimizer import OptunaOptimizer

OPTIONS = ["squared_hinge", "hinge"]
BEST_OPTION = "hinge"


class DummyModel:
    """Scores best at ``loss == BEST_OPTION`` with ``bootstrap`` on."""

    def __init__(self):
        self.loss = "squared_hinge"
        self.bootstrap = False
        self.C = 1.0
        self.trained_with = None

    def train(self, x, y, x_validation=None, y_validation=None):
        self.trained_with = (self.loss, self.bootstrap, self.C)

    def predict(self, dataset):
        return (1.0 if self.loss == BEST_OPTION else 0.0) + (
            0.5 if self.bootstrap else 0.0
        )

    def calculate_metrics(self, split=None, level=None):
        assert split in (SplitEnum.TRAIN, SplitEnum.VALIDATION)
        assert level is LevelEnum.TRIAL

    def prepare_output(self, dataset, is_fit=False):
        return dataset


class DummyMetric:
    @staticmethod
    def score(y_true, y_pred):
        return y_pred


@pytest.fixture
def dataset():
    return {"train": [0], "validation": [0]}


def _strategy(model, input_dataset, output_dataset, metric):
    model.train(input_dataset["train"], output_dataset["train"])
    return metric.score(
        model.prepare_output(output_dataset["validation"], is_fit=False),
        model.predict(input_dataset["validation"]),
    )


def _parameters(model):
    """What ``ModelFactory`` reports for a categorical and a boolean field."""
    return [
        (model, "loss", OPTIONS, "categorical"),
        (model, "bootstrap", [False, True], "categorical"),
    ]


def _run(optimizer, model, dataset, parameters=None):
    optimizer.optimize(
        model,
        dataset,
        dataset,
        parameters if parameters is not None else _parameters(model),
        {"class": DummyMetric, "metadata": {"maximize": True}},
        _strategy,
    )
    return optimizer


# --------------------------------------------------------------------------- #
# What ModelFactory hands over
# --------------------------------------------------------------------------- #


def test_the_options_are_read_from_the_envelope():
    space = _search_space_of(
        {"x-dashai-search-dtype": "categorical"},
        {"optimize": True, "choices": OPTIONS, "fixed_value": "hinge"},
    )
    assert space == (OPTIONS, "categorical")


def test_an_interval_still_arrives_as_a_pair():
    space = _search_space_of(
        {"x-dashai-search-dtype": "number"},
        {"optimize": True, "lower_bound": 0.1, "upper_bound": 0.9},
    )
    assert space == ((0.1, 0.9), "number")


def test_the_declared_dtype_wins_over_the_json_schema_type():
    """A categorical field is a string on the wire, and ``type`` would say so."""
    space = _search_space_of(
        {"x-dashai-search-dtype": "categorical", "type": "string"},
        {"optimize": True, "choices": OPTIONS},
    )
    assert space.dtype == "categorical"


def test_a_field_declared_the_old_way_still_reads_its_type():
    space = _search_space_of(
        {"type": "integer"}, {"optimize": True, "lower_bound": 1, "upper_bound": 9}
    )
    assert space == ((1, 9), "integer")


def test_a_nullable_field_no_longer_loses_its_dtype():
    """``none_type(...)`` emits ``anyOf`` and no ``type``, so the old read
    returned None and optuna refused the parameter as unsupported."""
    old_style = {"anyOf": [{"type": "integer"}, {"type": "null"}]}
    assert _search_space_of(old_style, {"optimize": True}).dtype is None
    declared = {**old_style, "x-dashai-search-dtype": "integer"}
    assert _search_space_of(declared, {"optimize": True}).dtype == "integer"


# --------------------------------------------------------------------------- #
# Optuna
# --------------------------------------------------------------------------- #


def test_optuna_searches_the_options_and_finds_the_best(dataset):
    model = DummyModel()
    optimizer = _run(
        OptunaOptimizer(n_trials=20, sampler="RandomSampler", pruner=None),
        model,
        dataset,
    )
    assert optimizer.get_best_params() == {"loss": BEST_OPTION, "bootstrap": True}
    assert model.loss == BEST_OPTION
    assert model.bootstrap is True


def test_optuna_never_proposes_an_option_outside_the_set(dataset):
    model = DummyModel()
    seen = set()
    original = DummyModel.train

    def record(self, *args, **kwargs):
        seen.add(self.loss)
        return original(self, *args, **kwargs)

    DummyModel.train = record
    try:
        _run(
            OptunaOptimizer(n_trials=15, sampler="RandomSampler", pruner=None),
            model,
            dataset,
        )
    finally:
        DummyModel.train = original
    assert seen <= set(OPTIONS)


def test_optuna_mixes_a_categorical_with_an_interval(dataset):
    """Both kinds land in the same slot of the tuple, so they must coexist."""
    model = DummyModel()
    parameters = [
        (model, "loss", OPTIONS, "categorical"),
        (model, "C", (0.1, 10.0), "number"),
    ]
    _run(
        OptunaOptimizer(n_trials=15, sampler="RandomSampler", pruner=None),
        model,
        dataset,
        parameters,
    )
    assert model.loss in OPTIONS
    assert 0.1 <= model.C <= 10.0


def test_optuna_still_refuses_a_dtype_it_does_not_know(dataset):
    """As a TypeError, so it is not swallowed as an unfittable trial.

    ``study.optimize`` catches ValueError, so a ValueError here came back as
    "every one of the N trials failed, narrow the ranges and try again", which
    is the wrong thing to tell someone whose declaration is what is wrong.
    """
    model = DummyModel()
    with pytest.raises(TypeError, match="Unsupported parameter type"):
        _run(
            OptunaOptimizer(n_trials=3, sampler="RandomSampler", pruner=None),
            model,
            dataset,
            [(model, "loss", OPTIONS, "colour")],
        )


# --------------------------------------------------------------------------- #
# Hyperopt
# --------------------------------------------------------------------------- #


def test_hyperopt_searches_the_options_and_finds_the_best(dataset):
    model = DummyModel()
    optimizer = _run(HyperOptOptimizer(n_trials=25, sampler="tpe"), model, dataset)
    assert optimizer.get_best_params() == {"loss": BEST_OPTION, "bootstrap": True}
    assert model.loss == BEST_OPTION


def test_hyperopt_reports_the_option_and_not_its_index(dataset):
    """This is the bug the old ``float(raw_value)`` produced: hyperopt hands
    back ``1`` for the second option, so the final model was set to ``1.0``."""
    model = DummyModel()
    optimizer = _run(HyperOptOptimizer(n_trials=10, sampler="tpe"), model, dataset)

    assert isinstance(model.loss, str)
    assert model.loss in OPTIONS
    assert isinstance(model.bootstrap, bool)

    for trial in optimizer.get_trials_values():
        assert trial["params"]["loss"] in OPTIONS, trial
        assert trial["params"]["bootstrap"] in (False, True), trial


def test_hyperopt_still_coerces_the_numeric_kinds(dataset):
    model = DummyModel()
    parameters = [
        (model, "loss", OPTIONS, "categorical"),
        (model, "C", (0.1, 10.0), "number"),
    ]
    optimizer = _run(
        HyperOptOptimizer(n_trials=12, sampler="tpe"), model, dataset, parameters
    )
    best = optimizer.get_best_params()
    assert isinstance(best["C"], float)
    assert isinstance(best["loss"], str)


def test_hyperopt_refuses_an_unknown_dtype_rather_than_dropping_it(dataset):
    """It used to leave the parameter out of the space and report a study that
    had optimized nothing."""
    model = DummyModel()
    with pytest.raises(TypeError, match="Unsupported parameter type"):
        _run(
            HyperOptOptimizer(n_trials=3, sampler="tpe"),
            model,
            dataset,
            [(model, "loss", OPTIONS, "colour")],
        )
