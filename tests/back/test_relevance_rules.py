"""Relevance dependencies that used to live only in a field's description.

A sentence in a description is documentation: nothing reads it and nothing
enforces it. Fifteen fields carried one, and the measurement that mattered was
which of them could become a rule *today*:

* Five could, and now have: the seed-and-shuffle dependency in the five
  splitters that take both, plus the covariance explorer's delta degrees of
  freedom. Their conditions read a plain boolean sibling.
* Two cannot, because their condition is not in the schema at all. The two
  `constant` converters say "only used when a single column is selected", and
  how many columns the user selected is session state. That needs the context
  channel.
* One could not because of the value model, and is covered separately in
  test_exponential_smoothing_rules.py.
* Three were not dependencies at all: my sweep matched "at 0.0 the depth map
  has no effect", which describes what a value means rather than what it
  depends on.

The five splitters share one rule object rather than five copies of the same
sentence, which is what this file checks first.
"""

import pytest

from DashAI.back.core.schema_fields import check_rules
from DashAI.back.core.schema_fields.base_schema import RULES_KEY
from DashAI.back.core.utils import MultilingualString, localize
from DashAI.back.dependencies.config_builder import get_initial_components
from DashAI.back.splitters.rules import SEED_ONLY_MATTERS_WHEN_SHUFFLING

#: Every splitter that takes both a shuffle flag and a seed.
SEEDED_SPLITTERS = [
    "HoldoutSplitter",
    "KFoldSplitter",
    "StratifiedKFoldSplitter",
    "StratifiedGroupKFoldSplitter",
    "GroupKFoldSplitter",
]


def _component(name: str) -> type:
    for component in get_initial_components():
        if getattr(component, "__name__", None) == name:
            return component
    raise AssertionError(f"{name} is not registered")


def _defaults(component: type) -> dict:
    return {
        name: prop.get("placeholder")
        for name, prop in component.get_schema()["properties"].items()
    }


# --------------------------------------------------------------------------- #
# The seed and shuffle dependency, five splitters, one rule
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("name", SEEDED_SPLITTERS)
def test_the_seed_is_irrelevant_without_shuffling(name: str):
    component = _component(name)
    report = check_rules(component.SCHEMA, {**_defaults(component), "shuffle": False})
    assert report.irrelevant_fields() == ["random_state"]
    assert report.relevance["random_state"]["effect"] == "disable"


@pytest.mark.parametrize("name", SEEDED_SPLITTERS)
def test_the_seed_is_relevant_with_shuffling(name: str):
    component = _component(name)
    report = check_rules(component.SCHEMA, {**_defaults(component), "shuffle": True})
    assert report.irrelevant_fields() == []


@pytest.mark.parametrize("name", SEEDED_SPLITTERS)
def test_the_dependency_left_the_prose(name: str):
    """It was the same two sentences in five languages in five files."""
    properties = _component(name).get_schema()["properties"]
    for field in ("shuffle", "random_state"):
        description = properties[field]["description"]
        for language in ("en", "es", "pt", "de", "zh"):
            text = getattr(description, language) or ""
            for phrase in (
                "no effect",
                "ignored when",
                "no tiene efecto",
                "Se ignora",
                "não tem efeito",
                "keine Wirkung",
                "Wird ignoriert",
                "不起作用",
                "将被忽略",
            ):
                assert phrase not in text, (name, field, language, text)


@pytest.mark.parametrize("name", SEEDED_SPLITTERS)
def test_all_five_use_the_same_rule_object(name: str):
    """Not five copies of one sentence.

    A rule is stateless, so one instance can be listed by several schemas. Each
    still has its field names checked against its own fields, so listing it on a
    schema without a `shuffle` field would fail at import.
    """
    rules = _component(name).SCHEMA.__dashai_rules__
    assert SEED_ONLY_MATTERS_WHEN_SHUFFLING in rules, name


def test_the_shared_reason_is_multilingual():
    reason = SEED_ONLY_MATTERS_WHEN_SHUFFLING.reason
    assert isinstance(reason, MultilingualString)
    for language in ("en", "es", "pt", "de", "zh"):
        assert getattr(reason, language)


@pytest.mark.parametrize("name", SEEDED_SPLITTERS)
def test_the_rule_reaches_the_wire(name: str):
    schema = localize(_component(name).get_schema(), "es")
    relevance = [rule for rule in schema[RULES_KEY] if rule.get("kind") == "relevance"]
    assert len(relevance) == 1, name
    assert relevance[0]["field"] == "random_state"
    assert "estado aleatorio" in relevance[0]["reason"]


def test_a_splitter_without_shuffle_declares_no_such_rule():
    """The repeated folds always shuffle, so there is nothing to depend on."""
    for name in ("RepeatedKFoldSplitter", "RepeatedStratifiedKFoldSplitter"):
        component = _component(name)
        properties = component.get_schema()["properties"]
        assert "random_state" in properties
        assert "shuffle" not in properties
        assert SEED_ONLY_MATTERS_WHEN_SHUFFLING not in (
            component.SCHEMA.__dashai_rules__ or ()
        )


# --------------------------------------------------------------------------- #
# The covariance explorer, where declaration order would have broken a validator
# --------------------------------------------------------------------------- #


def test_the_delta_degrees_of_freedom_follow_numeric_only():
    component = _component("CovarianceMatrixExplorer")
    defaults = _defaults(component)

    on = check_rules(component.SCHEMA, {**defaults, "numeric_only": True})
    assert on.irrelevant_fields() == []

    off = check_rules(component.SCHEMA, {**defaults, "numeric_only": False})
    assert off.irrelevant_fields() == ["delta_degree_of_freedom"]


def test_the_controlling_field_is_declared_after_the_one_it_controls():
    """Which is exactly why this is a rule and not a field_validator.

    ``@field_validator`` reads ``info.data``, which holds only the fields
    validated before it. ``delta_degree_of_freedom`` comes first here, so a
    validator on it would find ``numeric_only`` absent and quietly do nothing —
    the same silent no-op the chunkers avoid only by luck of ordering. A rule
    runs on the complete model.
    """
    fields = list(_component("CovarianceMatrixExplorer").SCHEMA.model_fields)
    assert fields.index("delta_degree_of_freedom") < fields.index("numeric_only")


# --------------------------------------------------------------------------- #
# What is still prose, and why
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("name", ["ColumnArithmetic", "ColumnConcat"])
def test_the_constant_converters_still_wait_for_the_context_channel(name: str):
    """Their condition is not a field, so no rule can express it yet.

    "Only used (and required) when a single column is selected" depends on how
    many columns the user picked, which is session state rather than a schema
    field. It needs the context channel, so the sentence stays in the prose
    until then — and this test says so, rather than leaving the omission to look
    like an oversight.
    """
    component = _component(name)
    properties = component.get_schema()["properties"]
    assert "constant" in properties
    # There is no sibling carrying the column count, which is the whole problem.
    assert not {"column_count", "columns", "selected_columns"} & set(properties)
    description = properties["constant"]["description"]
    assert "single column is selected" in description.en
