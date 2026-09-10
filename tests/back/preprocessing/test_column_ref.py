import pytest

from DashAI.back.preprocessing.column_ref import (
    ConverterSequence,
    ConverterStep,
    GroupColumnRef,
    RawColumnRef,
    parse_column_refs,
    resolve_refs,
)


def test_raw_ref_resolves_to_its_own_name():
    assert resolve_refs([RawColumnRef(name="age")], {}) == ["age"]


def test_group_ref_resolves_to_that_steps_produced_columns():
    refs = [RawColumnRef(name="age"), GroupColumnRef(step=0)]
    resolved = resolve_refs(refs, {0: ["bow_apple", "bow_banana"]})
    assert resolved == ["age", "bow_apple", "bow_banana"]


def test_group_ref_to_an_unfit_step_raises_key_error():
    with pytest.raises(KeyError):
        resolve_refs([GroupColumnRef(step=0)], {})


def test_slotted_group_ref_resolves_to_only_that_types_columns():
    refs = [GroupColumnRef(step=0, slot="Categorical")]
    resolved_columns = {0: ["most_frequent_city", "imputed_age"]}
    resolved_slots = {
        0: {
            "Categorical": ["most_frequent_city"],
            "Integer": ["imputed_age"],
        }
    }
    assert resolve_refs(refs, resolved_columns, resolved_slots) == [
        "most_frequent_city"
    ]


def test_slotted_group_ref_with_no_resolved_slots_raises_key_error():
    with pytest.raises(KeyError):
        resolve_refs([GroupColumnRef(step=0, slot="Categorical")], {0: ["x"]})


def test_slotted_group_ref_to_a_type_the_step_never_produced_raises_key_error():
    with pytest.raises(KeyError):
        resolve_refs(
            [GroupColumnRef(step=0, slot="Text")],
            {0: ["x"]},
            {0: {"Integer": ["x"]}},
        )


def test_unslotted_group_ref_still_resolves_to_every_column_when_slots_exist():
    refs = [GroupColumnRef(step=0)]
    resolved_columns = {0: ["most_frequent_city", "imputed_age"]}
    resolved_slots = {
        0: {
            "Categorical": ["most_frequent_city"],
            "Integer": ["imputed_age"],
        }
    }
    assert resolve_refs(refs, resolved_columns, resolved_slots) == [
        "most_frequent_city",
        "imputed_age",
    ]


def test_sequence_rejects_a_step_referencing_itself_or_later():
    sequence = ConverterSequence(
        steps=[
            ConverterStep(
                converter="Binarizer",
                params={},
                scope=[GroupColumnRef(step=0)],
            )
        ]
    )
    with pytest.raises(ValueError, match="not strictly before"):
        sequence.validate_scopes()


def test_sequence_accepts_a_step_referencing_an_earlier_one():
    sequence = ConverterSequence(
        steps=[
            ConverterStep(
                converter="BagOfWordsConverter",
                params={},
                scope=[RawColumnRef(name="text")],
            ),
            ConverterStep(
                converter="StandardScaler",
                params={},
                scope=[GroupColumnRef(step=0)],
            ),
        ]
    )
    sequence.validate_scopes()  # does not raise


def test_parse_column_refs_round_trips_json_dicts():
    raw = [{"kind": "raw", "name": "age"}, {"kind": "group", "step": 2}]
    parsed = parse_column_refs(raw)
    assert parsed == [RawColumnRef(name="age"), GroupColumnRef(step=2)]


def test_parse_column_refs_round_trips_a_slotted_group_ref():
    raw = [{"kind": "group", "step": 0, "slot": "Categorical"}]
    parsed = parse_column_refs(raw)
    assert parsed == [GroupColumnRef(step=0, slot="Categorical")]


def test_converter_sequence_model_dump_round_trips():
    sequence = ConverterSequence(
        steps=[
            ConverterStep(
                converter="Binarizer",
                params={"threshold": 0.5},
                scope=[RawColumnRef(name="age")],
            )
        ]
    )
    dumped = sequence.model_dump(mode="json")
    restored = ConverterSequence.model_validate(dumped)
    assert restored == sequence
