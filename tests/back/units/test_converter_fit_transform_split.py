"""Fitting a converter on one dataset and applying it to another.

The point of splitting ``ApplyConverterUnit`` into ``FitConverterUnit`` +
``TransformDatasetUnit``: a scaler, encoder or imputer must learn its statistics
from the training data only and then be applied unchanged to the test data.
Refitting on test would leak the test distribution into the evaluation, which is
exactly what the fused unit forced.
"""

import pandas as pd
import pyarrow as pa
import pytest
from kink import di

from DashAI.back.converters.scikit_learn.min_max_scaler import MinMaxScaler
from DashAI.back.dataloaders.classes.dashai_dataset import to_dashai_dataset
from DashAI.back.job.base_job import JobError
from DashAI.back.types.value_types import Float
from DashAI.back.units.apply_converter_unit import ApplyConverterUnit
from DashAI.back.units.context import ExecutionContext, UnitContractError
from DashAI.back.units.fit_converter_unit import FitConverterUnit
from DashAI.back.units.transform_dataset_unit import TransformDatasetUnit

FULL_SCOPE = {"columns": [], "rows": []}


def _dataset(**columns):
    frame = pd.DataFrame(columns)
    types = {name: Float(arrow_type=pa.float64()) for name in frame.columns}
    return to_dashai_dataset(frame, types=types)


def _values(dataset, column="a"):
    return list(dataset.to_pandas()[column])


@pytest.fixture(name="registry")
def fixture_registry():
    registry = {"MinMaxScaler": {"class": MinMaxScaler}}
    di["component_registry"] = registry
    yield registry
    del di["component_registry"]


def test_a_converter_fitted_on_train_is_applied_to_test_without_refitting(registry):
    """The headline case.

    MinMaxScaler fitted on [0, 5, 10] learns min=0, max=10. Applied to a test
    value of 20 it must yield 2.0 — outside [0, 1] precisely because the range
    came from train. A refit on the test data would have produced 0.0 instead,
    so the number is what proves the fitted state survived.
    """
    ctx = ExecutionContext()

    # Fit on train.
    ctx.put("dataset", _dataset(a=[0.0, 5.0, 10.0]))
    FitConverterUnit(
        converter={"component": "MinMaxScaler", "params": {}},
        scope=FULL_SCOPE,
        target=None,
    )(ctx)

    # Transform train with it.
    TransformDatasetUnit(scope=FULL_SCOPE, target=None)(ctx)
    assert _values(ctx.require("dataset")) == [0.0, 0.5, 1.0]

    # Swap in the test dataset and transform with the *same* fitted converter.
    ctx.put("dataset", _dataset(a=[20.0]))
    TransformDatasetUnit(scope=FULL_SCOPE, target=None)(ctx)

    assert _values(ctx.require("dataset")) == [2.0]


def test_fitting_leaves_the_dataset_untouched(registry):
    """FitConverterUnit produces a converter, not data."""
    ctx = ExecutionContext()
    original = _dataset(a=[0.0, 5.0, 10.0])
    ctx.put("dataset", original)

    FitConverterUnit(
        converter={"component": "MinMaxScaler", "params": {}},
        scope=FULL_SCOPE,
        target=None,
    )(ctx)

    assert ctx.require("dataset") is original
    assert _values(ctx.require("dataset")) == [0.0, 5.0, 10.0]


def test_the_fitted_converter_is_published_live_not_copied(registry):
    """It has to be the same object, or the learned state would be lost."""
    ctx = ExecutionContext()
    ctx.put("dataset", _dataset(a=[0.0, 10.0]))

    FitConverterUnit(
        converter={"component": "MinMaxScaler", "params": {}},
        scope=FULL_SCOPE,
        target=None,
    )(ctx)

    fitted = ctx.require("fitted_converter")
    assert isinstance(fitted, MinMaxScaler)
    assert ctx.require("fitted_converter") is fitted
    # The learned statistics are what makes it worth reusing.
    assert list(fitted.data_min_) == [0.0]
    assert list(fitted.data_max_) == [10.0]


def test_transforming_without_a_fitted_converter_is_a_contract_error():
    """A missing converter is a wiring mistake, not "nothing to apply"."""
    ctx = ExecutionContext()
    ctx.put("dataset", _dataset(a=[1.0]))

    with pytest.raises(UnitContractError, match="'fitted_converter' is not available"):
        TransformDatasetUnit(scope=FULL_SCOPE, target=None)(ctx)


def test_transforming_without_a_dataset_is_a_contract_error(registry):
    ctx = ExecutionContext()
    ctx.put("fitted_converter", MinMaxScaler())

    with pytest.raises(UnitContractError, match="'dataset' is not available"):
        TransformDatasetUnit(scope=FULL_SCOPE, target=None)(ctx)


def test_the_fused_unit_also_publishes_its_fitted_converter(registry):
    """ApplyConverterUnit stays usable as the source of a reusable converter.

    So the single-dataset path and the train/test path are the same mechanism:
    whoever fitted the converter publishes it, and any number of
    TransformDatasetUnits can then apply it elsewhere.
    """
    ctx = ExecutionContext()
    ctx.put("dataset", _dataset(a=[0.0, 5.0, 10.0]))

    ApplyConverterUnit(
        converter={"component": "MinMaxScaler", "params": {}},
        scope=FULL_SCOPE,
        target=None,
    )(ctx)

    assert _values(ctx.require("dataset")) == [0.0, 0.5, 1.0]

    ctx.put("dataset", _dataset(a=[20.0]))
    TransformDatasetUnit(scope=FULL_SCOPE, target=None)(ctx)

    assert _values(ctx.require("dataset")) == [2.0]


def test_the_split_pair_matches_the_fused_unit_on_a_single_dataset(registry):
    """The two paths must not drift: same input, same output."""
    fused_ctx = ExecutionContext()
    fused_ctx.put("dataset", _dataset(a=[1.0, 2.0, 3.0, 4.0]))
    ApplyConverterUnit(
        converter={"component": "MinMaxScaler", "params": {}},
        scope=FULL_SCOPE,
        target=None,
    )(fused_ctx)

    split_ctx = ExecutionContext()
    split_ctx.put("dataset", _dataset(a=[1.0, 2.0, 3.0, 4.0]))
    FitConverterUnit(
        converter={"component": "MinMaxScaler", "params": {}},
        scope=FULL_SCOPE,
        target=None,
    )(split_ctx)
    TransformDatasetUnit(scope=FULL_SCOPE, target=None)(split_ctx)

    assert _values(fused_ctx.require("dataset")) == _values(
        split_ctx.require("dataset")
    )


def test_a_row_scope_narrows_the_fit_but_the_transform_still_sees_every_row(registry):
    """Row scope belongs to fitting; transform always covers the dataset.

    Fitting on rows 1-2 of [0, 10, 100] learns min=0, max=10, so the third row
    scales to 10.0 rather than 1.0.
    """
    ctx = ExecutionContext()
    ctx.put("dataset", _dataset(a=[0.0, 10.0, 100.0]))

    FitConverterUnit(
        converter={"component": "MinMaxScaler", "params": {}},
        scope={"columns": [], "rows": [1, 2]},
        target=None,
    )(ctx)
    TransformDatasetUnit(scope=FULL_SCOPE, target=None)(ctx)

    assert _values(ctx.require("dataset")) == [0.0, 1.0, 10.0]


def test_fit_names_the_culprit_when_the_converter_is_not_registered(registry):
    ctx = ExecutionContext()
    ctx.put("dataset", _dataset(a=[1.0]))

    with pytest.raises(JobError, match="Error importing converter NotRegistered"):
        FitConverterUnit(
            converter={"component": "NotRegistered", "params": {}},
            scope=FULL_SCOPE,
            target=None,
        )(ctx)


def test_fit_rejects_an_out_of_bounds_target_before_running(registry):
    ctx = ExecutionContext()
    ctx.put("dataset", _dataset(a=[1.0], b=[2.0]))
    unit = FitConverterUnit(
        converter={"component": "MinMaxScaler", "params": {}},
        scope=FULL_SCOPE,
        target={"idx": 99},
    )

    with pytest.raises(JobError, match="Target column index 99 is out of bounds"):
        unit.validate(ctx)

    assert not ctx.has("fitted_converter")


def test_two_fit_units_in_one_context_resolve_their_converters_independently(registry):
    """Registry lookups are memoized on the instance, never in the context."""

    class _Other(MinMaxScaler):
        pass

    registry["Other"] = {"class": _Other}

    ctx = ExecutionContext()
    ctx.put("dataset", _dataset(a=[0.0, 10.0]))

    first = FitConverterUnit(
        converter={"component": "MinMaxScaler", "params": {}},
        scope=FULL_SCOPE,
        target=None,
    )
    second = FitConverterUnit(
        converter={"component": "Other", "params": {}},
        scope=FULL_SCOPE,
        target=None,
    )
    first(ctx)
    second(ctx)

    assert first._converter_class is MinMaxScaler
    assert second._converter_class is _Other


def test_the_units_register_under_the_unit_type():
    """Guards the mixin's name.

    ``ConverterScopeMixin`` must not be called ``Base*``: the registry rejects a
    component whose MRO has more than one "Base" ancestor declaring a TYPE, so
    an intermediate ``BaseConverterUnit`` would break registration for all three
    converter units at once.
    """
    from DashAI.back.dependencies.registry import ComponentRegistry

    units = [ApplyConverterUnit, FitConverterUnit, TransformDatasetUnit]
    component_registry = ComponentRegistry(initial_components=units)

    for unit in units:
        assert component_registry[unit.__name__]["type"] == "Unit"


def test_one_fitted_converter_feeds_several_transforms(registry):
    """Nothing about a transform consumes or invalidates the fitted converter."""
    ctx = ExecutionContext()
    ctx.put("dataset", _dataset(a=[0.0, 10.0]))
    FitConverterUnit(
        converter={"component": "MinMaxScaler", "params": {}},
        scope=FULL_SCOPE,
        target=None,
    )(ctx)

    for value, expected in ((5.0, 0.5), (20.0, 2.0), (-10.0, -1.0)):
        ctx.put("dataset", _dataset(a=[value]))
        TransformDatasetUnit(scope=FULL_SCOPE, target=None)(ctx)
        assert _values(ctx.require("dataset")) == [expected]
