import pandas as pd

from DashAI.back.converters.imbalanced_learn.smote_converter import SMOTEConverter
from DashAI.back.converters.scikit_learn.pca import PCA
from DashAI.back.converters.scikit_learn.select_k_best import SelectKBest
from DashAI.back.converters.scikit_learn.standard_scaler import StandardScaler
from DashAI.back.converters.simple_converters.date_features import (
    DateFeaturesConverter,
)
from DashAI.back.converters.simple_converters.nan_remover import NanRemover
from DashAI.back.converters.simple_converters.time_resampler import (
    TimeResamplerConverter,
)
from DashAI.back.dataloaders.classes.dashai_dataset import (
    to_dashai_dataset,
    transform_dataset_with_schema,
)
from DashAI.back.preprocessing.column_ref import (
    ConverterSequence,
    ConverterStep,
    GroupColumnRef,
    RawColumnRef,
)
from DashAI.back.preprocessing.session_preprocessor import SessionPreprocessor
from DashAI.back.preprocessing.structure import infer_structure
from DashAI.back.preprocessing.structure_types import BlockItem, ColumnItem
from DashAI.back.splitters.splits_payload import schema_placeholder_defaults

REGISTRY = {
    cls.__name__: {"class": cls}
    for cls in (
        PCA,
        SelectKBest,
        StandardScaler,
        DateFeaturesConverter,
        SMOTEConverter,
        NanRemover,
        TimeResamplerConverter,
    )
}

SCHEMA = {
    "age": {"type": "Integer", "dtype": "int64"},
    "height": {"type": "Float", "dtype": "float64"},
    "city": {"type": "Categorical", "dtype": "string"},
    "date": {"type": "Date", "dtype": "%Y-%m-%d"},
    "date_year": {"type": "Integer", "dtype": "int64"},
    "label": {"type": "Categorical", "dtype": "string"},
}


def _dataset():
    frame = pd.DataFrame(
        {
            "age": [30, 41, 25, 60],
            "height": [1.7, 1.8, 1.6, 1.75],
            "city": ["a", "b", "a", "c"],
            "date": ["2024-01-05", "2024-02-10", "2024-03-15", "2024-04-20"],
            "date_year": [1, 2, 3, 4],
            "label": ["yes", "no", "yes", "no"],
        }
    )
    return transform_dataset_with_schema(to_dashai_dataset(frame), SCHEMA)


def _infer(steps, candidates=("age", "height", "city", "date"), target=("label",)):
    return infer_structure(
        dataset_types=_dataset().types,
        candidates=list(candidates),
        target=list(target),
        steps=steps,
        component_registry=REGISTRY,
    )


def _step(converter, scope, **params):
    return ConverterStep(converter=converter, params=params, scope=scope)


def _names(state):
    return [item.name for item in state if isinstance(item, ColumnItem)]


def test_initial_state_is_the_candidates_without_the_target():
    result = _infer([], candidates=["age", "label", "city"])

    assert _names(result.initial) == ["age", "city"]
    assert result.final == result.initial
    assert result.valid


def test_a_consumed_column_cannot_be_used_by_a_later_step():
    result = _infer(
        [
            _step(
                "PCA",
                [RawColumnRef(name="age"), RawColumnRef(name="height")],
                n_components=2,
            ),
            _step("StandardScaler", [RawColumnRef(name="age")]),
        ]
    )

    first, second = result.steps
    assert first.status == "ok"
    assert "age" not in _names(first.state)
    (block,) = first.added
    assert isinstance(block, BlockItem)
    assert (block.step, block.slot, block.count) == (0, None, 2)
    assert second.status == "error"
    assert second.error.code == "missing_ref"
    assert not result.valid


def test_the_target_cannot_be_in_a_scope():
    result = _infer([_step("StandardScaler", [RawColumnRef(name="label")])])

    assert result.steps[0].error.code == "target_in_scope"


def test_steps_after_a_broken_one_are_blocked():
    result = _infer(
        [
            _step("StandardScaler", [RawColumnRef(name="missing")]),
            _step("StandardScaler", [RawColumnRef(name="age")]),
        ]
    )

    assert [step.status for step in result.steps] == ["error", "blocked"]
    assert _names(result.final) == ["age", "height", "city", "date"]


def test_an_unknown_converter_is_an_error():
    result = _infer([_step("Nope", [RawColumnRef(name="age")])])

    assert result.steps[0].error.code == "unknown_converter"


def test_a_scope_type_the_converter_does_not_accept_is_an_error():
    result = _infer([_step("StandardScaler", [RawColumnRef(name="city")])])

    assert result.steps[0].error.code == "type_not_allowed"


def test_row_changing_converters_without_a_split_rule_are_not_supported():
    params = schema_placeholder_defaults(TimeResamplerConverter)
    result = _infer(
        [_step("TimeResamplerConverter", [RawColumnRef(name="date")], **params)]
    )

    assert result.steps[0].error.code == "rows_not_supported"


def test_a_resampler_keeps_its_scope_and_drops_every_other_column():
    result = _infer(
        [
            _step(
                "SMOTEConverter",
                [RawColumnRef(name="age"), RawColumnRef(name="height")],
                random_state=0,
            )
        ]
    )

    step = result.steps[0]
    assert step.status == "ok"
    assert _names(step.state) == ["age", "height"]
    codes = [warning.code for warning in step.warnings]
    assert codes == ["train_only", "drops_columns"]
    assert step.warnings[1].params == {"columns": ["city", "date"]}


def test_more_components_than_columns_is_an_error():
    result = _infer(
        [
            _step(
                "PCA",
                [RawColumnRef(name="age"), RawColumnRef(name="height")],
                n_components=5,
            )
        ]
    )

    error = result.steps[0].error
    assert error.code == "n_components_exceeds"
    assert error.params == {"n_components": 5, "columns": 2}


def test_a_named_generated_column_can_be_used_by_a_later_step():
    result = _infer(
        [
            _step("DateFeaturesConverter", [RawColumnRef(name="date")]),
            _step("StandardScaler", [GroupColumnRef(step=0, name="date_month")]),
        ]
    )

    assert result.valid
    month = next(item for item in result.final if item.name == "date_month")
    assert (month.type, month.origin) == ("Float", 0)


def test_a_selector_over_mixed_types_adds_one_slotted_block_per_type():
    result = _infer(
        [
            _step(
                "SelectKBest",
                [RawColumnRef(name="age"), RawColumnRef(name="height")],
                k=1,
            ),
        ]
    )

    blocks = result.steps[0].added
    assert {(block.slot, block.type) for block in blocks} == {
        ("Integer", "Integer"),
        ("Float", "Float"),
    }


def test_a_clashing_new_column_is_renamed_like_the_runtime_does():
    # "date_year" exists in the dataset but is not a candidate, so the one
    # DateFeatures creates must become "date_year_1", as the runtime names it.
    step = _step("DateFeaturesConverter", [RawColumnRef(name="date")])

    estimated = _infer([step])

    preprocessor = SessionPreprocessor(ConverterSequence(steps=[step]), REGISTRY)
    _, resolved = preprocessor.fit_transform({"train": _dataset()})
    added = [item.name for item in estimated.steps[0].added]
    assert added[0] == "date_year_1"
    assert added == resolved[0]


class _BrokenEstimateConverter(StandardScaler):
    """Stands in for a plugin whose structure estimate crashes."""

    def get_output_type(self, column_name=None):
        raise RuntimeError("no idea")


def test_a_crashing_estimate_falls_back_to_one_unknown_block():
    registry = {**REGISTRY, "Broken": {"class": _BrokenEstimateConverter}}

    result = infer_structure(
        dataset_types=_dataset().types,
        candidates=["age", "height"],
        target=["label"],
        steps=[_step("Broken", [RawColumnRef(name="age")])],
        component_registry=registry,
    )

    step = result.steps[0]
    assert step.status == "ok"
    assert [w.code for w in step.warnings] == ["inference_fallback"]
    (block,) = step.added
    assert (block.type, block.count) == (None, None)
    assert _names(step.state) == ["height"]


def test_nan_remover_keeps_its_scope_and_warns_it_removes_rows_everywhere():
    result = _infer([_step("NanRemover", [RawColumnRef(name="age")])])

    step = result.steps[0]
    assert step.status == "ok"
    assert _names(step.state) == ["age"]
    codes = [warning.code for warning in step.warnings]
    assert codes == ["rows_removed_in_splits", "drops_columns"]
