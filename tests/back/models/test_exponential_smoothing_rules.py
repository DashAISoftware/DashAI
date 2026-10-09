"""The season-length dependency, and the half of it that cannot move yet.

``ExponentialSmoothing`` carried both halves of one dependency in two places
that the form could not see:

* ``season_length`` is meaningless without a seasonal component. That lived as a
  sentence in the field's description, in five languages, enforced nowhere. It
  is now a ``Relevance`` rule, so the control is disabled and says why.
* A seasonal component needs a season length of at least 2, because a season of
  1 repeats every observation. That lives in ``__init__`` and raises at
  construction time, which for a forecasting model means inside a worker.

The second one **cannot** become a ``Check`` today, and this file pins that
rather than leaving it as a comment. ``season_length`` is a search space, so its
value is the ``{optimize, fixed_value, lower_bound, upper_bound}`` envelope
rather than a number, and the algebra refuses a non-number by design: the rule
would evaluate to pending forever and never fire. ``validate_rules`` therefore
refuses to accept it at all, which is what turns "this will silently not work"
into "this fails at import".

Giving the search space a declared type did not lift that: the value the rule
would read is a ``SearchSpace`` either way. What it did settle is the other
direction — the guard is why ``ExponentialSmoothing.seasonal`` is one of the few
enums left unsearchable, since a ``Relevance`` here reads it and a rule over an
envelope cannot fire. Try to search it and the class stops importing.
"""

import pytest

from DashAI.back.core.schema_fields import (
    BaseSchema,
    Check,
    F,
    Ne,
    Relevance,
    RuleDeclarationError,
    check_rules,
    enum_field,
    int_field,
    schema_field,
    search_space,
)
from DashAI.back.core.schema_fields.base_schema import RULES_KEY
from DashAI.back.core.utils import MultilingualString, localize
from DashAI.back.models.forecasting.exponential_smoothing import (
    ExponentialSmoothing,
    ExponentialSmoothingSchema,
)

ENVELOPE = {
    "optimize": False,
    "fixed_value": 12,
    "lower_bound": 2,
    "upper_bound": 12,
}


def _defaults():
    return {
        name: prop.get("placeholder")
        for name, prop in ExponentialSmoothing.get_schema()["properties"].items()
    }


# --------------------------------------------------------------------------- #
# The half that moved
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("seasonal", ["add", "mul"])
def test_the_season_length_is_relevant_with_a_seasonal_component(seasonal: str):
    report = check_rules(
        ExponentialSmoothingSchema, {**_defaults(), "seasonal": seasonal}
    )
    assert report.irrelevant_fields() == []


def test_the_season_length_is_irrelevant_without_one():
    """statsmodels spells "no seasonality" as the string "none", not as null."""
    report = check_rules(
        ExponentialSmoothingSchema, {**_defaults(), "seasonal": "none"}
    )
    assert report.irrelevant_fields() == ["season_length"]
    state = report.relevance["season_length"]
    assert state["effect"] == "disable"
    assert "seasonal component" in state["reason"].get("en")


def test_the_rule_reaches_the_wire_localized():
    schema = localize(ExponentialSmoothing.get_schema(), "es")
    rules = schema[RULES_KEY]
    assert [rule["kind"] for rule in rules] == ["relevance"]
    assert rules[0]["field"] == "season_length"
    assert "componente estacional" in rules[0]["reason"]


def test_the_prose_no_longer_carries_the_dependency():
    """It was a sentence in five languages that nothing enforced."""
    description = ExponentialSmoothing.get_schema()["properties"]["season_length"][
        "description"
    ]
    for language in ("en", "es", "pt", "de", "zh"):
        text = getattr(description, language)
        assert "nly used when" not in text
        assert "Solo se usa" not in text


# --------------------------------------------------------------------------- #
# The half that cannot move, and why
# --------------------------------------------------------------------------- #


def test_a_check_over_an_optimizer_field_is_refused_at_class_definition():
    with pytest.raises(RuleDeclarationError) as raised:

        class WouldNeverFire(BaseSchema):
            seasonal: schema_field(
                enum_field(["none", "add", "mul"]), "none", description="d"
            )  # type: ignore
            season_length: search_space(
                int_field(ge=1), fixed=12, low=2, high=12, description="d"
            )  # type: ignore

            rules = [
                Check(
                    F("season_length") >= 2,
                    id="season.length_at_least_two",
                    targets=["season_length"],
                    message=MultilingualString(en="At least 2."),
                )
            ]

    message = str(raised.value)
    assert "optimizer envelope" in message
    assert "never fire" in message
    # And it says what to do instead, since the author cannot act on a refusal
    # they do not understand.
    assert "has to stay in a validator" in message


def test_a_relevance_targeting_an_optimizer_field_is_still_allowed():
    """Targeting is not reading: the condition is what gets evaluated."""

    class Fine(BaseSchema):
        seasonal: schema_field(
            enum_field(["none", "add", "mul"]), "none", description="d"
        )  # type: ignore
        season_length: search_space(
            int_field(ge=1), fixed=12, low=2, high=12, description="d"
        )  # type: ignore

        rules = [Relevance("season_length", when=Ne(F("seasonal"), "none"))]

    report = check_rules(Fine, {"seasonal": "none", "season_length": ENVELOPE})
    assert report.irrelevant_fields() == ["season_length"]


def test_the_minimum_is_still_enforced_where_it_can_be():
    """Refusing the rule must not mean losing the constraint."""
    ExponentialSmoothing(trend="none", seasonal="add", season_length=12)
    ExponentialSmoothing(trend="none", seasonal="none", season_length=1)

    with pytest.raises(ValueError, match="season length of at least 2"):
        ExponentialSmoothing(trend="none", seasonal="add", season_length=1)


def test_the_shipped_default_would_break_that_rule_if_seasonality_were_on():
    """Why the two halves are not interchangeable.

    The declared default is ``fixed_value: 1`` with ``seasonal: "none"``, which
    is consistent only because the season length is irrelevant there. A user who
    turns seasonality on without raising the length gets the ``__init__`` error,
    and the form cannot warn them first for exactly the reason above.
    """
    defaults = _defaults()
    assert defaults["seasonal"] == "none"
    assert defaults["season_length"]["fixed_value"] == 1
