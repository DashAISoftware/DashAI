"""Every range a schema splits into two fields must declare its ordering.

When the underlying library takes a range as one tuple — ``feature_range``,
``ngram_range``, ``percentiles``, a pair of Canny thresholds — the schema cannot
express a tuple, so the pair is split into two form fields. Splitting it drops
the one thing the tuple guaranteed: that the low end comes first.

Ten pairs did that and none of them checked. The failure modes, measured rather
than assumed:

* ``MinMaxScaler`` and the vectorizers raise a ``ValueError`` from inside
  scikit-learn, which for a converter or a model means inside a Huey worker,
  long after the form said the configuration was fine.
* ``partial_dependence`` raises too, at explanation time.
* ``cv2.Canny`` raises nothing at all and returns the same edges either way, so
  an inverted pair is silently wrong. That is the worse one: the user never
  finds out.

The relation is not always the same, and each was checked against the library
rather than guessed: ``min_df``/``max_df`` and ``ngram_range`` accept equal
values, ``feature_range`` and ``percentiles`` require the low end to be strictly
smaller.

This test is written against the pairs rather than against a rule id, so it
keeps holding if a rule is renamed, and it fails loudly if someone adds a new
split range without an ordering rule.
"""

from typing import Any, Dict, Tuple

import pytest
from pydantic import ValidationError

from DashAI.back.core.schema_fields.base_schema import RULES_KEY
from DashAI.back.dependencies.config_builder import get_initial_components

#: component -> (low field, high field, whether equal values are allowed)
RANGE_PAIRS: Dict[str, Tuple[str, str, bool]] = {
    "MinMaxScaler": ("min_range", "max_range", False),
    "TFIDFVectorizerModel": ("min_df", "max_df", True),
    "BM25VectorizerModel": ("min_df", "max_df", True),
    "TFIDFConverter": ("lower_bound_ngrams", "upper_bound_ngrams", True),
    "BagOfWordsConverter": ("lower_bound_ngrams", "upper_bound_ngrams", True),
    "BagOfWordsTextClassificationModel": ("ngram_min_n", "ngram_max_n", True),
    "TfIdfLogRegTextClassificationModel": ("ngram_min_n", "ngram_max_n", True),
    "PartialDependence": ("lower_percentile", "upper_percentile", False),
    "RegressionPartialDependence": ("lower_percentile", "upper_percentile", False),
    "SDXLCannyControlNetModel": (
        "canny_low_threshold",
        "canny_high_threshold",
        False,
    ),
}


def _component(name: str) -> type:
    for component in get_initial_components():
        if getattr(component, "__name__", None) == name:
            return component
    raise AssertionError(f"{name} is not registered")


def _defaults(component: type) -> Dict[str, Any]:
    return {
        name: prop.get("placeholder")
        for name, prop in component.get_schema()["properties"].items()
    }


def _is_integer(component: type, field: str) -> bool:
    prop = component.get_schema()["properties"][field]
    branches = prop.get("anyOf") or [prop]
    return any(branch.get("type") == "integer" for branch in branches)


def _pair(component: type, low_field: str, low: Any, high: Any) -> Dict[str, Any]:
    high_field = RANGE_PAIRS[component.__name__][1]
    return {low_field: low, high_field: high}


@pytest.mark.parametrize("name", sorted(RANGE_PAIRS))
def test_the_pair_declares_an_ordering_rule(name: str):
    component = _component(name)
    schema = component.get_schema()
    assert RULES_KEY in schema, (
        f"{name} splits a range into two fields and declares no rules, so "
        "nothing stops the low end from being above the high end."
    )
    low_field, high_field, _ = RANGE_PAIRS[name]
    targeted = {
        target
        for rule in schema[RULES_KEY]
        if rule.get("kind") == "check"
        for target in rule["targets"]
    }
    assert {low_field, high_field} <= targeted, (
        f"{name} has rules but none of them reports on both {low_field} and "
        f"{high_field}, so the message would appear under only one of the two "
        "fields the relation is about."
    )


@pytest.mark.parametrize("name", sorted(RANGE_PAIRS))
def test_an_inverted_pair_is_rejected(name: str):
    component = _component(name)
    low_field, _, _ = RANGE_PAIRS[name]
    low, high = (5, 1) if _is_integer(component, low_field) else (0.9, 0.1)

    with pytest.raises(ValidationError) as raised:
        component.SCHEMA.model_validate(
            {**_defaults(component), **_pair(component, low_field, low, high)}
        )
    # The message must be the rule's, not a bound or type error that happens to
    # fire on the same values.
    assert any(
        "smaller" in error["msg"] or "cannot be greater" in error["msg"]
        for error in raised.value.errors()
    ), raised.value.errors()


@pytest.mark.parametrize("name", sorted(RANGE_PAIRS))
def test_equal_values_follow_the_library(name: str):
    """Half these libraries accept a degenerate range and half do not."""
    component = _component(name)
    low_field, _, equal_allowed = RANGE_PAIRS[name]
    value = 1 if _is_integer(component, low_field) else 0.5
    payload = {**_defaults(component), **_pair(component, low_field, value, value)}

    if equal_allowed:
        component.SCHEMA.model_validate(payload)
        return
    with pytest.raises(ValidationError):
        component.SCHEMA.model_validate(payload)


@pytest.mark.parametrize("name", sorted(RANGE_PAIRS))
def test_the_declared_defaults_satisfy_their_own_rule(name: str):
    """A shipped default that breaks its own rule would block every form."""
    component = _component(name)
    low_field, high_field, _ = RANGE_PAIRS[name]
    defaults = _defaults(component)
    low, high = defaults[low_field], defaults[high_field]
    assert isinstance(low, (int, float)), (name, low_field, low)
    assert isinstance(high, (int, float)), (name, high_field, high)
    assert low <= high, f"{name} ships {low_field}={low} above {high_field}={high}"


def test_the_rules_are_localized_like_every_other_message():
    """A constraint message is user-facing text and gets the same languages."""
    from DashAI.back.core.utils import MultilingualString

    for name in RANGE_PAIRS:
        for rule in _component(name).get_schema()[RULES_KEY]:
            message = rule.get("message")
            if message is None:
                continue
            assert isinstance(message, MultilingualString), (name, rule.get("id"))
            for language in ("en", "es", "pt", "de", "zh"):
                assert getattr(message, language), (name, rule.get("id"), language)
