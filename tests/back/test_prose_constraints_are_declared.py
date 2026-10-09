"""A constraint stated in a description must also be declared in the schema.

A field description is documentation: nothing reads it, nothing enforces it, and
it is written once per language. So a sentence like "Must be a multiple of 8" is
a constraint that exists only for whoever happens to read the tooltip. 28
properties across the diffusion models said exactly that, in five languages,
and a width of 513 sailed through the form into the pipeline.

The keywords for those constraints already exist and cost nothing: ``multipleOf``
is standard JSON Schema and pydantic emits and enforces it from
``int_field(multiple_of=...)``, and a numeric range is just ``ge``/``le``. This
test keeps prose and declaration from drifting apart again, by reading the
descriptions the same way a user would and checking the schema agrees.

Deliberately narrow: it only judges constraints the schema layer can actually
express on that field. A range described for the *elements* of a comma-separated
list typed into a text box is real documentation that no keyword on a string
field can capture, and the exceptions below name those rather than weakening the
check.
"""

import re
from typing import Any, Dict, List, Tuple

import pytest

from DashAI.back.dependencies.config_builder import get_initial_components

#: Fields whose description states a constraint on parsed content rather than on
#: the field's own value, so no keyword on the declared type could express it.
#: Each entry needs a reason, not just a name.
CONTENT_CONSTRAINT_EXCEPTIONS = {
    # `none_type(string_field())` holding "25, 50, 75": the range applies to the
    # integers parsed out of the text, and a string field has no numeric bound.
    # Validating the contents needs a list type, which is a separate problem.
    ("DescribeExplorer", "percentiles"),
}

NUMERIC_TYPES = {"integer", "number"}


def _numeric_branch(prop: Dict[str, Any]) -> Dict[str, Any]:
    """The numeric branch of a property, or an empty dict if it has none."""
    for branch in prop.get("anyOf") or [prop]:
        if branch.get("type") in NUMERIC_TYPES:
            return branch
    return {}


def _english(prop: Dict[str, Any]) -> str:
    description = prop.get("description")
    if hasattr(description, "en"):
        return description.en or ""
    return description if isinstance(description, str) else ""


def _properties() -> List[Tuple[str, str, Dict[str, Any]]]:
    rows = []
    for component in get_initial_components():
        if not hasattr(component, "get_schema"):
            continue
        try:
            properties = component.get_schema().get("properties", {})
        except Exception:
            continue
        for name, prop in properties.items():
            rows.append((component.__name__, name, prop))
    return rows


PROPERTIES = _properties()

MULTIPLE_OF_CASES = [
    (component, name, prop, int(match.group(1)))
    for component, name, prop in PROPERTIES
    if (match := re.search(r"multiple of (\d+)", _english(prop), re.I))
]

RANGE_CASES = [
    (component, name, prop, int(match.group(1)), int(match.group(2)))
    for component, name, prop in PROPERTIES
    if (match := re.search(r"between (\d+) and (\d+)", _english(prop), re.I))
]


def test_there_is_something_to_check():
    """A silent zero here would make both checks below vacuous."""
    assert len(MULTIPLE_OF_CASES) > 20, len(MULTIPLE_OF_CASES)
    assert len(RANGE_CASES) > 5, len(RANGE_CASES)


@pytest.mark.parametrize(
    ("component", "name", "prop", "factor"),
    MULTIPLE_OF_CASES,
    ids=[f"{c}.{n}" for c, n, _, _ in MULTIPLE_OF_CASES],
)
def test_a_described_multiple_is_also_declared(
    component: str, name: str, prop: Dict[str, Any], factor: int
):
    branch = _numeric_branch(prop)
    if not branch:
        pytest.skip(f"{component}.{name} is not numeric; nothing to declare on")
    assert branch.get("multipleOf") == factor, (
        f"{component}.{name} tells the user the value must be a multiple of "
        f"{factor} and declares multipleOf={branch.get('multipleOf')!r}. Pass "
        f"multiple_of={factor} to int_field so pydantic and the form enforce "
        "what the description promises."
    )


@pytest.mark.parametrize(
    ("component", "name", "prop", "low", "high"),
    RANGE_CASES,
    ids=[f"{c}.{n}" for c, n, _, _, _ in RANGE_CASES],
)
def test_a_described_range_matches_the_declared_bounds(
    component: str, name: str, prop: Dict[str, Any], low: int, high: int
):
    if (component, name) in CONTENT_CONSTRAINT_EXCEPTIONS:
        pytest.skip(f"{component}.{name} constrains parsed content, not the field")
    branch = _numeric_branch(prop)
    if not branch:
        pytest.skip(f"{component}.{name} is not numeric; nothing to declare on")
    declared = (branch.get("minimum"), branch.get("maximum"))
    assert declared == (low, high), (
        f"{component}.{name} tells the user the value is between {low} and "
        f"{high} and declares {declared}. Either the bounds or the sentence is "
        "wrong, and the user only ever sees the sentence."
    )
