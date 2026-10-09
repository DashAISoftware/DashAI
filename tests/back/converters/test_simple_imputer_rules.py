"""The SimpleImputer's strategy/fill_value dependency, declared as rules.

`fill_value` is the second real relevance case in the tree and it is a harder
one than the holdout seed: the condition is an enum value rather than a boolean,
the field it governs is a four-branch union, and the dependency was documented
nowhere at all, not even in the field's own description.

What scikit-learn 1.7.2 actually does, measured rather than assumed:

    strategy="mean",     fill_value=99   -> imputes 1.5, the 99 is discarded
    strategy="median",   fill_value=99   -> imputes 1.5
    strategy="constant", fill_value=99   -> imputes 99
    strategy="constant", fill_value=None -> imputes 0, without asking

So a value the user typed and dashAI persisted is silently dropped for three of
the four strategies, and the fourth invents a default. Both facts are now rules.
"""

import pytest
from pydantic import ValidationError

from DashAI.back.converters.scikit_learn.simple_imputer import (
    SimpleImputer,
    SimpleImputerSchema,
)
from DashAI.back.core.schema_fields import check_rules
from DashAI.back.core.schema_fields.base_schema import RULES_KEY
from DashAI.back.core.utils import MultilingualString, localize

BASE = {"add_indicator": False, "keep_empty_features": False}


def params(**overrides):
    return {**BASE, **overrides}


@pytest.mark.parametrize("strategy", ["mean", "median", "most_frequent"])
def test_a_fill_value_is_accepted_but_marked_irrelevant(strategy):
    """It stays in the payload, inert.

    Rejecting it would be hostile: the natural way to reach this state is to
    type a fill value under "constant" and then change your mind about the
    strategy. sklearn ignores it, so the form disables it and says why.
    """
    values = params(strategy=strategy, fill_value=99)
    SimpleImputerSchema.model_validate(values)

    report = check_rules(SimpleImputerSchema, values)
    assert report.irrelevant_fields() == ["fill_value"]
    assert report.ok


@pytest.mark.parametrize("strategy", ["mean", "median", "most_frequent"])
def test_the_constant_check_does_not_run_for_other_strategies(strategy):
    """A check whose target is irrelevant must not fire.

    This is the composition the rule layer is built on: the Check below carries
    no strategy condition of its own, and does not need one.
    """
    report = check_rules(SimpleImputerSchema, params(strategy=strategy))
    assert report.violations == []
    assert report.pending == []


def test_constant_requires_a_fill_value():
    with pytest.raises(ValidationError) as raised:
        SimpleImputerSchema.model_validate(params(strategy="constant", fill_value=None))
    assert 'The "constant" strategy needs a fill value' in str(raised.value)


def test_constant_with_a_fill_value_passes():
    SimpleImputerSchema.model_validate(params(strategy="constant", fill_value=99))
    report = check_rules(
        SimpleImputerSchema, params(strategy="constant", fill_value=99)
    )
    assert report.ok
    assert report.irrelevant_fields() == []


def test_every_union_branch_is_a_valid_fill_value():
    """The field is int | float | str | null, and all four must keep working."""
    for value in (99, 1.5, "unknown"):
        SimpleImputerSchema.model_validate(
            params(strategy="constant", fill_value=value)
        )


def test_a_type_incompatible_fill_value_is_still_out_of_reach():
    """Documented gap, not an oversight.

    ``fill_value="x"`` on a numeric column raises inside sklearn at fit time,
    in a Huey worker. Catching it needs the dataset's column dtypes, which is
    the context channel (C6) and a later phase. Asserting it here keeps the
    limitation visible instead of letting someone assume it is covered.
    """
    SimpleImputerSchema.model_validate(params(strategy="constant", fill_value="x"))


def test_the_rules_reach_the_wire_localized():
    schema = localize(SimpleImputer.get_schema(), "es")
    rules = schema[RULES_KEY]
    assert len(rules) == 2

    relevance = next(rule for rule in rules if rule["kind"] == "relevance")
    assert relevance["field"] == "fill_value"
    assert relevance["effect"] == "disable"
    assert 'estrategia "constant"' in relevance["reason"]

    check = next(rule for rule in rules if rule["kind"] == "check")
    assert check["id"] == "simple_imputer.constant_needs_fill_value"
    assert check["targets"] == ["fill_value"]
    assert "valor de relleno" in check["message"]


def test_the_messages_are_multilingual_before_localization():
    """A constraint message gets the same five languages as a label."""
    rules = SimpleImputer.get_schema()[RULES_KEY]
    for rule in rules:
        text = rule.get("message") or rule.get("reason")
        assert isinstance(text, MultilingualString)
        for language in ("en", "es", "pt", "de", "zh"):
            assert getattr(text, language)


def test_the_other_properties_are_untouched():
    """Declaring rules must not disturb the fields themselves."""
    schema = SimpleImputer.get_schema()
    assert set(schema["properties"]) == {
        "strategy",
        "fill_value",
        "add_indicator",
        "keep_empty_features",
    }
    fill_value = schema["properties"]["fill_value"]
    assert [branch["type"] for branch in fill_value["anyOf"]] == [
        "integer",
        "number",
        "string",
        "null",
    ]
    assert fill_value["placeholder"] is None
