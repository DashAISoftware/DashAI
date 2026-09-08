"""Which parameters a user is offered the chance to optimize, and which not.

Thirty-one fields were declared ``none_type(optimizer_int_field(...))``, back
when that factory existed, which forces ``placeholder=None`` and erases the only
signal that made a field optimizable. They could not be optimized however they
were declared, and the first reading of that was that thirty-one searches had
been lost.

Reading them by name says something else. Sixteen are ``random_state`` and two
are ``n_jobs``: a seed and a thread count. Optimizing a seed is fitting noise,
and the accident that erased the signal is the only reason the product never
offered to do it. So the audit goes both ways — thirteen parameters gained a
search space, and eighteen declarations stopped claiming something they should
never have claimed.

What this file protects is that split. It is a tripwire rather than a
specification: the point is that a future declaration cannot quietly put a seed
back in the search, and cannot quietly drop a real hyperparameter out of it.
"""

import pytest

from DashAI.back.core.schema_fields.search_space import SEARCH_DTYPE_KEY
from DashAI.back.dependencies.config_builder import get_initial_components

#: Never a hyperparameter, whatever the model.
#:
#: A seed does not have a better value, it has a value that happens to score
#: better on this split, which is the definition of overfitting the search. A
#: thread count changes how long the fit takes and nothing about the fit.
NEVER_SEARCHABLE = {"random_state", "n_jobs"}

#: The thirteen revived by the audit, as (component, field).
REVIVED = [
    ("DecisionTreeRegression", "max_depth"),
    ("DecisionTreeRegression", "max_leaf_nodes"),
    ("ExtraTreesClassifier", "max_depth"),
    ("ExtraTreesRegression", "max_depth"),
    ("GradientBoostingClassifier", "max_depth"),
    ("GradientBoostingR", "max_depth"),
    ("GradientBoostingR", "max_leaf_nodes"),
    ("GradientBoostingR", "n_iter_no_change"),
    ("HistGradientBoostingRegression", "max_depth"),
    ("HistGradientBoostingRegression", "max_leaf_nodes"),
    ("RandomForestRegression", "max_depth"),
    ("RandomForestRegression", "max_leaf_nodes"),
    ("RandomForestRegression", "max_samples"),
]


def _properties() -> dict:
    out = {}
    for component in get_initial_components():
        if not hasattr(component, "get_schema"):
            continue
        try:
            out[component.__name__] = component.get_schema()["properties"]
        except Exception:
            continue
    return out


PROPERTIES = _properties()


def _is_search_space(prop: dict) -> bool:
    return prop.get(SEARCH_DTYPE_KEY) is not None


# --------------------------------------------------------------------------- #
# What must never be searchable
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("field", sorted(NEVER_SEARCHABLE))
def test_no_component_offers_to_optimize_it(field: str):
    offenders = [
        f"{name}.{field}"
        for name, properties in PROPERTIES.items()
        if field in properties and _is_search_space(properties[field])
    ]
    assert offenders == []


@pytest.mark.parametrize("field", sorted(NEVER_SEARCHABLE))
def test_it_is_still_an_editable_field(field: str):
    """Demoted, not removed: a user still sets a seed by hand."""
    holders = [name for name, props in PROPERTIES.items() if field in props]
    assert holders, field
    for name in holders:
        prop = PROPERTIES[name][field]
        assert not isinstance(prop.get("placeholder"), dict), f"{name}.{field}"


# --------------------------------------------------------------------------- #
# What the audit revived
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(("component", "field"), REVIVED, ids=lambda x: str(x))
def test_a_revived_parameter_declares_an_interval(component: str, field: str):
    prop = PROPERTIES[component][field]
    assert _is_search_space(prop), f"{component}.{field}"
    assert prop[SEARCH_DTYPE_KEY] in ("integer", "number")
    placeholder = prop["placeholder"]
    assert placeholder["lower_bound"] < placeholder["upper_bound"]


@pytest.mark.parametrize(("component", "field"), REVIVED, ids=lambda x: str(x))
def test_a_revived_parameter_still_admits_null(component: str, field: str):
    """``max_depth=None`` means no limit, and that stays the default.

    Reviving the search must not take away the value the model shipped with.
    """
    prop = PROPERTIES[component][field]
    branches = prop.get("anyOf") or []
    assert any(branch.get("type") == "null" for branch in branches), (
        f"{component}.{field} lost its null branch"
    )


@pytest.mark.parametrize(("component", "field"), REVIVED, ids=lambda x: str(x))
def test_a_revived_range_lies_inside_the_fields_own_bounds(component: str, field: str):
    """``search_space`` enforces this at import; this says so where it is read.

    ``GradientBoostingR.min_samples_leaf`` is the case that made it worth
    checking: declared over ``(0, 0.5]``, a fraction of the sample, and
    searched over ``1..20``, which are counts.
    """
    prop = PROPERTIES[component][field]
    branch = next(
        (b for b in (prop.get("anyOf") or [prop]) if b.get("type") != "null"), {}
    )
    placeholder = prop["placeholder"]
    for key in ("lower_bound", "upper_bound"):
        value = placeholder[key]
        if "minimum" in branch:
            assert value >= branch["minimum"], (component, field, key)
        if "exclusiveMinimum" in branch:
            assert value > branch["exclusiveMinimum"], (component, field, key)
        if "maximum" in branch:
            assert value <= branch["maximum"], (component, field, key)
        if "exclusiveMaximum" in branch:
            assert value < branch["exclusiveMaximum"], (component, field, key)


# --------------------------------------------------------------------------- #
# No field left half-declared
# --------------------------------------------------------------------------- #


def test_a_search_space_always_carries_its_envelope():
    """The failure mode the audit was about: a declaration that says a field is
    optimizable while its placeholder says nothing of the kind."""
    for name, properties in PROPERTIES.items():
        for field, prop in properties.items():
            if not _is_search_space(prop):
                continue
            placeholder = prop.get("placeholder")
            assert isinstance(placeholder, dict), f"{name}.{field}"
            assert "optimize" in placeholder, f"{name}.{field}"


def test_no_optimizable_field_is_declared_the_old_way_any_more():
    """Every envelope now comes from a declared type rather than by hand."""
    undeclared = [
        f"{name}.{field}"
        for name, properties in PROPERTIES.items()
        for field, prop in properties.items()
        if isinstance(prop.get("placeholder"), dict)
        and "optimize" in prop["placeholder"]
        and not _is_search_space(prop)
    ]
    assert undeclared == []
