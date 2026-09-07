"""The search space as a declared type rather than a shape of placeholder.

Two things were wrong with the mechanism this replaces, and both are the same
mistake: the only carrier of "this parameter can be optimized" was the shape of
its placeholder dict.

* ``optimizer_float_field`` was byte-for-byte ``float_field``, so the name
  declared an intent nothing acted on. Thirty-one fields were declared with one
  and wrapped in ``none_type``, which forces ``placeholder=None`` and erases
  the signal, so they could not be optimized however they were declared.
* The placeholder was a dict the field's own type knew nothing about, so no
  component accepted its own declared defaults and no bound was ever checked
  against the constraints of the field it belonged to.

Making it a type also lets a search space be something other than an interval.
``lower_bound``/``upper_bound`` can only describe a scale, and ``hinge`` is not
between ``squared_hinge`` and anything else, which is why HPO worked for ints
and floats only.
"""

import pytest
from pydantic import ValidationError

from DashAI.back.core.schema_fields import (
    BaseSchema,
    bool_field,
    enum_field,
    float_field,
    int_field,
    none_type,
    schema_field,
    search_space,
)
from DashAI.back.core.schema_fields.search_space import (
    SEARCH_DTYPE_KEY,
    SearchSpace,
    SearchSpaceDeclarationError,
)
from DashAI.back.core.schema_fields.utils import fill_objects
from DashAI.back.core.utils import MultilingualString, localize
from DashAI.back.dependencies.config_builder import get_initial_components


class Numeric(BaseSchema):
    rate: search_space(
        float_field(gt=0.0, le=1.0), fixed=0.1, low=0.01, high=1.0, description="d"
    )  # type: ignore
    depth: search_space(
        none_type(int_field(ge=1)), fixed=None, low=1, high=32, description="d"
    )  # type: ignore


class Categorical(BaseSchema):
    loss: search_space(
        enum_field(["squared_hinge", "hinge"]), fixed="squared_hinge", description="d"
    )  # type: ignore
    bootstrap: search_space(bool_field(), fixed=True, description="d")  # type: ignore
    class_weight: search_space(
        none_type(enum_field(["balanced"])), fixed=None, description="d"
    )  # type: ignore


def _defaults(schema: type) -> dict:
    return {
        name: prop["placeholder"]
        for name, prop in schema.model_json_schema()["properties"].items()
    }


# --------------------------------------------------------------------------- #
# The placeholder is derived, so it cannot disagree with the field
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("schema", [Numeric, Categorical])
def test_a_schema_accepts_its_own_declared_defaults(schema: type):
    """Which is the thing that has never been true.

    All thirty-one components with optimizable fields fail this today: the
    envelope is a dict, and the field is declared a number.
    """
    schema.model_validate(_defaults(schema))


def test_the_numeric_placeholder_carries_the_declared_interval():
    assert _defaults(Numeric)["rate"] == {
        "optimize": False,
        "fixed_value": 0.1,
        "lower_bound": 0.01,
        "upper_bound": 1.0,
    }


def test_the_categorical_placeholder_carries_the_declared_options():
    assert _defaults(Categorical)["loss"] == {
        "optimize": False,
        "fixed_value": "squared_hinge",
        "choices": ["squared_hinge", "hinge"],
    }


def test_the_dtype_is_declared_rather_than_inferred():
    """``type`` is absent whenever a field admits null, and cannot say
    "categorical" at all."""
    numeric = Numeric.model_json_schema()["properties"]
    categorical = Categorical.model_json_schema()["properties"]
    assert numeric["rate"][SEARCH_DTYPE_KEY] == "number"
    assert numeric["depth"][SEARCH_DTYPE_KEY] == "integer"
    assert "type" not in numeric["depth"]
    for field in ("loss", "bootstrap", "class_weight"):
        assert categorical[field][SEARCH_DTYPE_KEY] == "categorical"


# --------------------------------------------------------------------------- #
# The wire keeps the shape the renderer already reads
# --------------------------------------------------------------------------- #


def test_the_property_is_flat_rather_than_a_reference():
    """Left to itself pydantic emits ``$ref`` into ``$defs`` for a generic
    model, and the renderer reads ``type``, ``anyOf`` and ``enum`` straight off
    the property without resolving references."""
    schema = Numeric.model_json_schema()
    assert "$defs" not in schema
    assert schema["properties"]["rate"]["type"] == "number"
    assert schema["properties"]["rate"]["exclusiveMinimum"] == 0.0
    assert schema["properties"]["rate"]["maximum"] == 1.0


def test_a_migrated_field_emits_what_it_emitted_before():
    """The declaration changes; the wire does not, apart from the dtype key.

    ``title`` is excluded because it is not settled at this layer: pydantic puts
    the field name there, and ``get_schema`` replaces it with the declared alias
    or a name derived from the field. Both declarations reach that step the same
    way, and the next test checks the result on the real components.
    """

    class Before(BaseSchema):
        C: schema_field(
            float_field(gt=0.0),
            placeholder={
                "optimize": False,
                "fixed_value": 1.0,
                "lower_bound": 1.0,
                "upper_bound": 10.0,
            },
            description="d",
        )  # type: ignore

    class After(BaseSchema):
        C: search_space(
            float_field(gt=0.0), fixed=1.0, low=1.0, high=10.0, description="d"
        )  # type: ignore

    before = Before.model_json_schema()["properties"]["C"]
    after = After.model_json_schema()["properties"]["C"]
    assert set(after) - set(before) == {SEARCH_DTYPE_KEY}
    for key in set(before) - {"title"}:
        assert before[key] == after[key], key


def test_every_declared_search_space_reaches_the_wire_complete():
    """What the renderer needs off the property, on the real components.

    A missing title leaves the control unlabelled, a missing placeholder leaves
    it without the optimize toggle, and a categorical space with no options has
    nothing to offer.
    """
    for component in get_initial_components():
        if not hasattr(component, "get_schema"):
            continue
        try:
            properties = component.get_schema()["properties"]
        except Exception:
            continue
        for name, prop in properties.items():
            dtype = prop.get(SEARCH_DTYPE_KEY)
            if dtype is None:
                continue
            where = f"{component.__name__}.{name}"
            assert dtype in ("number", "integer", "categorical"), where
            assert isinstance(prop.get("title"), MultilingualString), where
            placeholder = prop.get("placeholder")
            assert isinstance(placeholder, dict), where
            assert placeholder.get("optimize") is False, where
            if dtype == "categorical":
                assert len(placeholder.get("choices") or []) >= 2, where
            else:
                assert placeholder.get("lower_bound") is not None, where
                assert placeholder.get("upper_bound") is not None, where


def test_a_searchable_option_set_has_names_to_show():
    """The options-to-search control lists them, which is where a raw
    ``squared_epsilon_insensitive`` is least readable."""
    unnamed = []
    for component in get_initial_components():
        if not hasattr(component, "get_schema"):
            continue
        try:
            properties = component.get_schema()["properties"]
        except Exception:
            continue
        for name, prop in properties.items():
            if prop.get(SEARCH_DTYPE_KEY) != "categorical":
                continue
            branches = prop.get("anyOf") or [prop]
            branch = next((b for b in branches if b.get("enum")), None)
            if branch is not None and not branch.get("enumNames"):
                unnamed.append(f"{component.__name__}.{name}")
    assert unnamed == []


def test_the_enum_names_survive_and_localize():
    """The categorical control lists options by name, so it must keep them."""
    prop = localize(Categorical.model_json_schema(), "es")["properties"]["loss"]
    assert prop["enum"] == ["squared_hinge", "hinge"]
    assert prop["enumNames"] == ["Bisagra cuadrática", "Bisagra"]


def test_the_description_is_multilingual_like_any_other_field():
    class Described(BaseSchema):
        rate: search_space(
            float_field(gt=0.0),
            fixed=0.1,
            low=0.01,
            high=1.0,
            description=MultilingualString(en="Rate.", es="Tasa."),
        )  # type: ignore

    prop = localize(Described.model_json_schema(), "es")["properties"]["rate"]
    assert prop["description"] == "Tasa."


# --------------------------------------------------------------------------- #
# What the envelope now refuses
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    ("value", "message"),
    [
        ({"optimize": True, "lower_bound": 0.9, "upper_bound": 0.1}, "below"),
        ({"optimize": True, "lower_bound": 0.1}, "needs both lower_bound"),
        ({"optimize": True}, "both bounds or a list"),
        ({"optimize": False}, "needs a fixed_value"),
        ({"optimize": True, "lower_bnd": 0.1, "upper_bound": 0.9}, "not permitted"),
        (
            {"optimize": True, "lower_bound": 0.1, "upper_bound": 0.9, "choices": [1]},
            "not both",
        ),
    ],
)
def test_an_incoherent_numeric_envelope_is_refused(value: dict, message: str):
    with pytest.raises(ValidationError, match=message):
        Numeric.model_validate({**_defaults(Numeric), "rate": value})


def test_a_bound_outside_the_fields_own_constraints_is_refused():
    """The search used to be free to propose values the field rejects."""
    with pytest.raises(ValidationError) as excinfo:
        Numeric.model_validate(
            {
                **_defaults(Numeric),
                "rate": {"optimize": True, "lower_bound": -5, "upper_bound": 0.9},
            }
        )
    error = excinfo.value.errors()[0]
    assert error["loc"] == ("rate", "lower_bound")
    assert "greater than 0" in error["msg"]


def test_a_fractional_bound_on_an_integer_field_is_refused():
    with pytest.raises(ValidationError, match="valid integer"):
        Numeric.model_validate(
            {
                **_defaults(Numeric),
                "depth": {"optimize": True, "lower_bound": 1.5, "upper_bound": 32},
            }
        )


@pytest.mark.parametrize(
    ("value", "message"),
    [
        ({"optimize": True, "choices": ["hinge"]}, "at least two"),
        ({"optimize": True, "choices": ["hinge", "hinge"]}, "distinct"),
        ({"optimize": True, "choices": ["hinge", "hnge"]}, "not in the enum"),
        ({"optimize": True, "lower_bound": "a", "upper_bound": "z"}, "not in the enum"),
    ],
)
def test_an_incoherent_categorical_envelope_is_refused(value: dict, message: str):
    with pytest.raises(ValidationError, match=message):
        Categorical.model_validate({**_defaults(Categorical), "loss": value})


def test_a_searched_option_must_be_one_the_field_offers():
    with pytest.raises(ValidationError) as excinfo:
        Categorical.model_validate(
            {
                **_defaults(Categorical),
                "loss": {"optimize": True, "choices": ["squared_hinge", "hnge"]},
            }
        )
    assert excinfo.value.errors()[0]["loc"] == ("loss", "choices", 1)


# --------------------------------------------------------------------------- #
# Null as a value rather than an absence
# --------------------------------------------------------------------------- #


def test_a_nullable_field_can_be_fixed_at_null():
    """``max_depth=None`` means "no limit", which is a value."""
    Numeric.model_validate(
        {**_defaults(Numeric), "depth": {"optimize": False, "fixed_value": None}}
    )


def test_a_fixed_parameter_without_a_fixed_value_is_still_refused():
    """Absent is distinguished from null, so the nullable case above does not
    open a hole for a genuinely missing value."""
    with pytest.raises(ValidationError, match="needs a fixed_value"):
        Numeric.model_validate(
            {**_defaults(Numeric), "depth": {"optimize": False, "lower_bound": 1}}
        )


def test_null_is_one_of_the_options_of_a_nullable_enum():
    """sklearn's ``class_weight`` is ``none_type(enum_field(["balanced"]))``, and
    unweighted against balanced is the comparison worth searching. Read as a
    one-option enum it would look like nothing to search at all."""
    assert _defaults(Categorical)["class_weight"]["choices"] == [None, "balanced"]
    Categorical.model_validate(
        {
            **_defaults(Categorical),
            "class_weight": {"optimize": True, "choices": [None, "balanced"]},
        }
    )


def test_a_boolean_is_a_two_option_search():
    assert _defaults(Categorical)["bootstrap"]["choices"] == [False, True]
    Categorical.model_validate(
        {
            **_defaults(Categorical),
            "bootstrap": {"optimize": True, "choices": [False, True]},
        }
    )


# --------------------------------------------------------------------------- #
# Declarations that fail at import
# --------------------------------------------------------------------------- #


def test_a_range_the_field_would_reject_fails_at_import():
    """``GradientBoostingR.min_samples_leaf`` is declared with bounds ``(0,
    0.5]``, a fraction of the sample, and searched over ``1..20``, which are
    counts. Every trial proposed a value the field forbids."""
    with pytest.raises(SearchSpaceDeclarationError, match="field itself rejects"):

        class Contradiction(BaseSchema):
            min_samples_leaf: search_space(
                float_field(gt=0.0, le=0.5), fixed=1, low=1, high=20, description="d"
            )  # type: ignore


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"fixed": 0.5, "low": 1.0, "high": 0.1}, "below high"),
        ({"fixed": 0.5, "low": 0.1, "high": 0.1}, "below high"),
        ({"fixed": 0.5, "low": 0.1}, "both `low` and `high`"),
        ({"fixed": 0.5}, "both `low` and `high`"),
        ({"fixed": 0.5, "low": 0.1, "high": 0.9, "choices": [0.1]}, "not `choices`"),
    ],
)
def test_an_incoherent_numeric_declaration_fails_at_import(kwargs: dict, message: str):
    with pytest.raises(SearchSpaceDeclarationError, match=message):

        class Bad(BaseSchema):
            rate: search_space(float_field(gt=0.0, le=1.0), description="d", **kwargs)  # type: ignore


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"fixed": "hinge", "choices": ["hinge", "hnge"]}, "field itself rejects"),
        ({"fixed": "hinge", "low": 0, "high": 1}, "not `low`/`high`"),
        ({"fixed": "hinge", "choices": ["hinge"]}, "at least two"),
        ({"fixed": "hinge", "choices": ["hinge", "hinge"]}, "repeat"),
    ],
)
def test_an_incoherent_categorical_declaration_fails_at_import(
    kwargs: dict, message: str
):
    with pytest.raises(SearchSpaceDeclarationError, match=message):

        class Bad(BaseSchema):
            loss: search_space(
                enum_field(["squared_hinge", "hinge"]), description="d", **kwargs
            )  # type: ignore


# --------------------------------------------------------------------------- #
# Getting back out to the library underneath
# --------------------------------------------------------------------------- #


def test_a_bare_value_is_read_as_a_parameter_fixed_at_it():
    """``ModelFactory`` unwraps the envelope before instantiating a model, so a
    model's own ``__init__`` validates plain scalars."""
    instance = Numeric.model_validate({"rate": 0.5, "depth": 4})
    assert instance.rate.fixed_value == 0.5
    assert instance.rate.optimize is False
    assert instance.depth.fixed_value == 4


def test_fill_objects_resolves_the_envelope_to_the_value():
    """``fill_objects`` dumps the model into kwargs for the library underneath,
    which wants the number rather than the envelope."""
    instance = Categorical.model_validate(_defaults(Categorical))
    assert fill_objects(instance) == {
        "loss": "squared_hinge",
        "bootstrap": True,
        "class_weight": None,
    }


def test_resolve_is_the_fixed_value():
    space = SearchSpace[float].model_validate(
        {"optimize": True, "lower_bound": 0.1, "upper_bound": 0.9, "fixed_value": 0.5}
    )
    assert space.resolve() == 0.5
