from DashAI.back.converters.scikit_learn.simple_imputer import SimpleImputer
from DashAI.back.converters.scikit_learn.standard_scaler import StandardScaler


def test_default_get_output_slots_derives_one_slot_from_get_output_type():
    converter = StandardScaler()
    slots = converter.get_output_slots()
    assert len(slots) == 1
    assert slots[0]["slot"] == 0
    assert type(slots[0]["type"]).__name__ == "Float"


def test_default_classify_output_columns_puts_everything_in_slot_0():
    converter = StandardScaler()
    result = converter.classify_output_columns(["a", "b", "c"])
    assert result == {0: ["a", "b", "c"]}


def test_simple_imputer_without_indicator_has_one_slot():
    converter = SimpleImputer(strategy="mean", add_indicator=False)
    slots = converter.get_output_slots()
    assert len(slots) == 1


def test_simple_imputer_with_indicator_has_two_slots():
    converter = SimpleImputer(strategy="mean", add_indicator=True)
    slots = converter.get_output_slots()
    assert len(slots) == 2
    assert slots[0]["label"] == "imputed"
    assert slots[1]["label"] == "missing_indicator"
    assert type(slots[1]["type"]).__name__ == "Integer"


def test_simple_imputer_classifies_real_columns_by_missingindicator_prefix():
    converter = SimpleImputer(strategy="mean", add_indicator=True)
    result = converter.classify_output_columns(
        ["age", "income", "missingindicator_age", "missingindicator_income"]
    )
    assert result == {
        0: ["age", "income"],
        1: ["missingindicator_age", "missingindicator_income"],
    }


def test_get_metadata_output_slots_includes_type_name():
    # get_metadata() is a classmethod and constructs a default instance
    # internally (see the Paso 0 note in base_converter.py), so this only
    # exercises the single-slot, default-constructed case. SimpleImputer's
    # own default (add_indicator=False) is intentionally not covered here:
    # get_metadata() reporting only one slot for it regardless of what a
    # real, user-configured instance would later declare is a known,
    # deferred gap (see the design spec), not something this test asserts
    # around.
    metadata = StandardScaler.get_metadata()
    assert metadata["output_slots"] == [{"slot": 0, "label": "output", "type": "Float"}]
