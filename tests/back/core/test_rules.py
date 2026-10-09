"""Behaviour of the declarative rule layer on the server.

Three groups, in order of what would hurt most if it broke:

1. **Back-compat.** A schema that declares no rules must serve a document
   identical to the one it served before this layer existed, and an existing
   ``@model_validator`` must keep working. 194 in-tree schema classes and an
   unknown number of ``dashai-*`` packages on PyPI depend on that, and there is
   no version handshake through which they could be warned.
2. **Loud failure.** A rule that would never fire is worse than no rule,
   because nobody notices. A misspelled field name, a duplicate id or a message
   that cannot be localized has to fail at class-definition time.
3. **Semantics.** Relevance, pending verdicts and context handling, asserted
   here on the Python side and against the same fixture on the JavaScript side.
"""

import pytest
from pydantic import ValidationError, model_validator

from DashAI.back.config_object import ConfigObject
from DashAI.back.core.schema_fields import (
    Approx,
    BaseSchema,
    Check,
    Ctx,
    F,
    In,
    IsTrue,
    Relevance,
    RuleDeclarationError,
    RuleViolationError,
    Sum,
    bool_field,
    check_rules,
    float_field,
    int_field,
    schema_field,
    string_field,
    violations_payload,
)
from DashAI.back.core.schema_fields.base_schema import RULES_KEY
from DashAI.back.core.utils import MultilingualString, localize

MSG = MultilingualString(en="Must hold.", es="Debe cumplirse.")


def _msg(text: str = "Must hold.") -> MultilingualString:
    return MultilingualString(en=text, es=text)


class PlainSchema(BaseSchema):
    """A schema with no rules at all."""

    a: schema_field(int_field(ge=0), placeholder=1, description="a")  # type: ignore
    b: schema_field(int_field(ge=0), placeholder=2, description="b")  # type: ignore


class SumSchema(BaseSchema):
    """Three proportions that must describe the whole."""

    train: schema_field(float_field(ge=0, le=1), placeholder=0.6, description="train")  # type: ignore
    validation: schema_field(
        float_field(ge=0, le=1), placeholder=0.2, description="validation"
    )  # type: ignore
    test: schema_field(float_field(ge=0, le=1), placeholder=0.2, description="test")  # type: ignore
    shuffle: schema_field(bool_field(), placeholder=True, description="shuffle")  # type: ignore
    random_state: schema_field(int_field(ge=0), placeholder=42, description="seed")  # type: ignore

    rules = [
        Check(
            Approx(Sum("train", "validation", "test"), 1.0, tol=1e-6),
            id="sum_to_one",
            targets=["train", "validation", "test"],
            message=MultilingualString(
                en="Must sum to 1 (currently {total}).",
                es="Deben sumar 1 (actualmente {total}).",
            ),
            bindings={"total": Sum("train", "validation", "test")},
        ),
        Relevance("random_state", when=IsTrue(F("shuffle")), effect="disable"),
    ]


# --------------------------------------------------------------------------- #
# 1. Back-compat
# --------------------------------------------------------------------------- #


def test_a_schema_without_rules_emits_the_same_document_as_before():
    keys = set(PlainSchema.model_json_schema().keys())
    assert keys == {"description", "properties", "required", "title", "type"}
    assert RULES_KEY not in PlainSchema.model_json_schema()


def test_a_schema_with_rules_adds_exactly_one_root_key():
    schema = SumSchema.model_json_schema()
    assert set(schema.keys()) - {
        "description",
        "properties",
        "required",
        "title",
        "type",
    } == {RULES_KEY}
    # And the properties themselves are untouched: rules never rewrite a field.
    assert set(schema["properties"]) == {
        "train",
        "validation",
        "test",
        "shuffle",
        "random_state",
    }
    assert schema["properties"]["train"]["placeholder"] == 0.6


def test_the_base_docstring_is_not_served_as_a_description():
    """``ConfigObject.SCHEMA`` defaults to ``BaseSchema``.

    Before this was handled, five registered components shipped a commented-out
    method body to the browser as their user-facing description.
    """

    class Bare(ConfigObject):
        pass

    assert "description" not in Bare.get_schema()


def test_an_existing_model_validator_still_runs_alongside_the_rule_validator():
    calls = []

    class WithBoth(BaseSchema):
        """Has both a rule and a hand-written validator."""

        x: schema_field(int_field(ge=0), placeholder=1, description="x")  # type: ignore

        rules = [Check(F("x") > 0, id="x_positive", targets=["x"], message=MSG)]

        @model_validator(mode="after")
        def _own(self):
            calls.append(self.x)
            return self

    WithBoth.model_validate({"x": 5})
    assert calls == [5]

    with pytest.raises(ValidationError):
        WithBoth.model_validate({"x": 0})


def test_rules_are_not_pydantic_fields():
    """``rules`` is a ClassVar, so it never becomes a parameter of the component."""
    assert "rules" not in SumSchema.model_fields
    assert "rules" not in SumSchema.model_json_schema()["properties"]


def test_messages_ride_the_existing_localize_path():
    wire = localize(SumSchema.model_json_schema(), "es")
    check = next(r for r in wire[RULES_KEY] if r.get("id") == "sum_to_one")
    assert check["message"] == "Deben sumar 1 (actualmente {total})."


# --------------------------------------------------------------------------- #
# 2. Loud failure
# --------------------------------------------------------------------------- #


def test_a_misspelled_field_name_fails_at_class_definition():
    with pytest.raises(RuleDeclarationError) as raised:

        class Typo(BaseSchema):
            validation: schema_field(
                float_field(ge=0), placeholder=0.2, description="v"
            )  # type: ignore

            rules = [
                Check(
                    F("validaton") > 0, id="typo", targets=["validation"], message=MSG
                )
            ]

    assert "validaton" in str(raised.value)
    assert "Did you mean 'validation'?" in str(raised.value)


def test_a_misspelled_target_also_fails():
    with pytest.raises(RuleDeclarationError):

        class BadTarget(BaseSchema):
            a: schema_field(int_field(), placeholder=1, description="a")  # type: ignore

            rules = [Check(F("a") > 0, id="t", targets=["nope"], message=MSG)]


def test_duplicate_rule_ids_fail():
    with pytest.raises(RuleDeclarationError) as raised:

        class Dupes(BaseSchema):
            a: schema_field(int_field(), placeholder=1, description="a")  # type: ignore

            rules = [
                Check(F("a") > 0, id="same", targets=["a"], message=MSG),
                Check(F("a") < 10, id="same", targets=["a"], message=MSG),
            ]

    assert "same" in str(raised.value)


def test_a_rule_with_no_targets_fails():
    with pytest.raises(RuleDeclarationError):
        Check(F("a") > 0, id="nowhere", targets=[], message=MSG)


def test_a_plain_string_message_is_refused():
    """Every user-facing string in dashAI is multilingual; a rule message too."""
    with pytest.raises(RuleDeclarationError):
        Check(F("a") > 0, id="x", targets=["a"], message="not multilingual")


def test_a_bare_python_comparison_is_refused_with_a_useful_message():
    """``Eq(a, b)`` exists because ``a == b`` would silently evaluate to a bool."""
    with pytest.raises(RuleDeclarationError) as raised:
        Check(True, id="x", targets=["a"], message=MSG)
    assert "Eq(a, b)" in str(raised.value)


def test_an_unknown_relevance_effect_fails():
    with pytest.raises(RuleDeclarationError):
        Relevance("a", when=IsTrue(F("b")), effect="collapse")


# --------------------------------------------------------------------------- #
# 3. Semantics
# --------------------------------------------------------------------------- #


def test_the_server_enforces_a_cross_field_rule():
    SumSchema.model_validate(
        {
            "train": 0.6,
            "validation": 0.3,
            "test": 0.1,
            "shuffle": True,
            "random_state": 42,
        }
    )
    with pytest.raises(ValidationError) as raised:
        SumSchema.model_validate(
            {
                "train": 0.8,
                "validation": 0.3,
                "test": 0.3,
                "shuffle": True,
                "random_state": 42,
            }
        )
    assert "Must sum to 1 (currently 1.4)." in str(raised.value)


def test_a_violation_carries_a_per_field_payload():
    try:
        SumSchema.model_validate(
            {
                "train": 0.8,
                "validation": 0.3,
                "test": 0.3,
                "shuffle": True,
                "random_state": 42,
            }
        )
        raise AssertionError("should have raised")
    except ValidationError as error:
        cause = error.errors()[0].get("ctx", {}).get("error")
        payload = violations_payload(cause)
        assert len(payload) == 1
        assert payload[0]["rule_id"] == "sum_to_one"
        assert payload[0]["targets"] == ["train", "validation", "test"]
        assert isinstance(payload[0]["message"], MultilingualString)
        assert payload[0]["message"].get("es") == "Deben sumar 1 (actualmente 1.4)."


def test_relevance_excludes_a_field_from_the_checks_that_name_it():
    class Relevant(BaseSchema):
        seed: schema_field(int_field(), placeholder=0, description="seed")  # type: ignore
        shuffle: schema_field(bool_field(), placeholder=True, description="shuffle")  # type: ignore

        rules = [
            Check(
                F("seed") >= 0, id="seed_non_negative", targets=["seed"], message=MSG
            ),
            Relevance("seed", when=IsTrue(F("shuffle")), effect="disable"),
        ]

    with pytest.raises(ValidationError):
        Relevant.model_validate({"seed": -1, "shuffle": True})
    # With shuffling off the seed means nothing, so the rule about it is not
    # merely satisfied, it does not apply.
    Relevant.model_validate({"seed": -1, "shuffle": False})


def test_a_rule_reading_an_absent_field_is_pending_not_failed():
    report = check_rules(SumSchema, {"train": None, "validation": 0.3, "test": 0.1})
    assert report.violations == []
    assert report.pending == ["sum_to_one"]
    assert report.ok


def test_a_context_rule_is_pending_without_context_and_enforced_with_it():
    class NeedsCtx(BaseSchema):
        group_column: schema_field(string_field(), placeholder="a", description="col")  # type: ignore

        rules = [
            Check(
                In(F("group_column"), Ctx("columns")),
                id="column_exists",
                targets=["group_column"],
                message=_msg("{col} is not a column."),
                bindings={"col": F("group_column")},
                requires_ctx=True,
            )
        ]

    # No context: reported as unvalidated rather than quietly passed.
    NeedsCtx.model_validate({"group_column": "nope"})
    report = check_rules(NeedsCtx, {"group_column": "nope"})
    assert report.pending == ["column_exists"]

    with_ctx = check_rules(
        NeedsCtx, {"group_column": "nope"}, ctx={"columns": ["a", "b"]}
    )
    assert with_ctx.pending == []
    assert with_ctx.violations[0]["message"].get("en") == "nope is not a column."

    ok = check_rules(NeedsCtx, {"group_column": "a"}, ctx={"columns": ["a", "b"]})
    assert ok.ok


def test_rules_merge_down_an_inheritance_chain():
    class Parent(BaseSchema):
        a: schema_field(int_field(), placeholder=1, description="a")  # type: ignore

        rules = [Check(F("a") > 0, id="parent", targets=["a"], message=MSG)]

    class Child(Parent):
        rules = [Check(F("a") < 100, id="child", targets=["a"], message=MSG)]

    class Grandchild(Child):
        pass

    assert [r.id for r in Parent.__dashai_rules__] == ["parent"]
    assert [r.id for r in Child.__dashai_rules__] == ["parent", "child"]
    # A subclass that declares nothing inherits the merged set exactly once.
    assert [r.id for r in Grandchild.__dashai_rules__] == ["parent", "child"]

    with pytest.raises(ValidationError):
        Child.model_validate({"a": 0})
    with pytest.raises(ValidationError):
        Child.model_validate({"a": 200})
    Child.model_validate({"a": 5})


def test_an_inherited_rule_still_reaches_the_wire():
    class Parent(BaseSchema):
        a: schema_field(int_field(), placeholder=1, description="a")  # type: ignore

        rules = [Check(F("a") > 0, id="parent", targets=["a"], message=MSG)]

    class Child(Parent):
        pass

    ids = [r["id"] for r in Child.model_json_schema()[RULES_KEY] if "id" in r]
    assert ids == ["parent"]


def test_rule_violation_is_a_value_error_so_existing_callers_keep_working():
    """Every current caller catches ``ValidationError``; nothing else changes."""
    assert issubclass(RuleViolationError, ValueError)
