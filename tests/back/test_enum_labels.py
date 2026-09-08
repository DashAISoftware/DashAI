"""The shared vocabulary behind the option names a dropdown shows.

``enumNames`` is the key the renderer has always read to decide what to display
for an enum option, and until now nothing produced it: across 219 components it
was emitted zero times, so every dropdown in the product showed the raw Python
value in all five languages. ``friedman_mse``, ``char_wb``, ``C`` and ``F`` are
the right values to send and the wrong words to show.

Most of those vocabularies repeat: 216 unlabelled fields used only 110 distinct
option sets. So the name belongs to the option set rather than to the field, and
``enum_field`` consults a shared table when a schema declares no labels of its
own. That is what makes this a table rather than 126 edits.

What the tests below protect is mostly the boundaries: that a registered set is
internally consistent, that the ambiguous sets stay out, and that the two
families which must keep showing their raw value keep showing it.
"""

from typing import Dict, List, Tuple

import pytest

from DashAI.back.core.schema_fields import enum_field, schema_field
from DashAI.back.core.schema_fields.base_schema import BaseSchema
from DashAI.back.core.schema_fields.enum_labels import SHARED_ENUM_LABELS, labels_for
from DashAI.back.core.utils import MultilingualString, localize
from DashAI.back.dependencies.config_builder import get_initial_components

LANGUAGES = ("en", "es", "pt", "de", "zh")


def _enum_branches() -> List[Tuple[str, str, Dict]]:
    """(component, field, branch) for every branch of every enum in the tree."""
    rows = []
    for component in get_initial_components():
        if not hasattr(component, "get_schema"):
            continue
        try:
            properties = component.get_schema().get("properties", {})
        except Exception:
            continue
        for name, prop in properties.items():
            for branch in prop.get("anyOf") or [prop]:
                if branch.get("enum"):
                    rows.append((component.__name__, name, branch))
    return rows


BRANCHES = _enum_branches()


# --------------------------------------------------------------------------- #
# The table itself
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("options", sorted(SHARED_ENUM_LABELS, key=len))
def test_a_registered_set_names_only_its_own_options(options: Tuple[str, ...]):
    """A label for an option that is not in the set would never be shown."""
    labels = SHARED_ENUM_LABELS[options]
    stray = sorted(set(labels) - set(options))
    assert not stray, (options, stray)


@pytest.mark.parametrize("options", sorted(SHARED_ENUM_LABELS, key=len))
def test_every_registered_name_is_complete(options: Tuple[str, ...]):
    """A half-translated name shows an empty dropdown row in the missing language."""
    for option, label in SHARED_ENUM_LABELS[options].items():
        assert isinstance(label, MultilingualString), (options, option)
        for language in LANGUAGES:
            assert getattr(label, language), (options, option, language)


@pytest.mark.parametrize("options", [("auto",), ("all",)], ids=["auto", "all"])
def test_an_ambiguous_set_is_not_registered(options: Tuple[str, ...]):
    """One name cannot be right for two meanings.

    ``auto`` is offered by ``iterated_power``, where it means "pick the
    iteration count for me", and by ``sampling_strategy``, where it means
    "resample every class but the largest". ``all`` is the same story. Those
    keep their raw value, and their field descriptions carry the meaning.
    """
    assert options not in SHARED_ENUM_LABELS
    assert labels_for(options) == {}


def test_lookup_is_by_the_whole_set_in_order():
    """Two fields offering the same options in a different order are different sets."""
    assert labels_for(["sqrt", "log2"])
    assert labels_for(["log2", "sqrt"]) == {}
    assert labels_for(["sqrt"]) == {}
    assert labels_for([]) == {}


# --------------------------------------------------------------------------- #
# How it reaches the wire
# --------------------------------------------------------------------------- #


def test_a_schema_gets_the_shared_names_by_declaring_nothing():
    class Plain(BaseSchema):
        criterion: schema_field(
            enum_field(["friedman_mse", "squared_error"]),
            "friedman_mse",
            description="d",
        )  # type: ignore

    prop = localize(Plain.model_json_schema(), "es")["properties"]["criterion"]
    assert prop["enum"] == ["friedman_mse", "squared_error"]
    assert prop["enumNames"] == [
        "Error cuadrático medio de Friedman",
        "Error cuadrático medio",
    ]


def test_explicit_labels_win_over_the_shared_ones():
    class Override(BaseSchema):
        criterion: schema_field(
            enum_field(
                ["friedman_mse", "squared_error"],
                labels={"friedman_mse": MultilingualString(en="Friedman")},
            ),
            "friedman_mse",
            description="d",
        )  # type: ignore

    prop = localize(Override.model_json_schema(), "en")["properties"]["criterion"]
    # The unnamed option still falls back to its own value.
    assert prop["enumNames"] == ["Friedman", "squared_error"]


def test_an_unregistered_set_emits_no_key_at_all():
    """Absent rather than a list of raw values, so nothing changes for it."""

    class Unknown(BaseSchema):
        mode: schema_field(enum_field(["wibble", "wobble"]), "wibble", description="d")  # type: ignore

    assert "enumNames" not in Unknown.model_json_schema()["properties"]["mode"]


@pytest.mark.parametrize(
    ("component", "field", "branch"),
    [(c, f, b) for c, f, b in BRANCHES if b.get("enumNames")],
    ids=[f"{c}.{f}" for c, f, b in BRANCHES if b.get("enumNames")],
)
def test_names_line_up_with_the_options_they_name(
    component: str, field: str, branch: Dict
):
    """The renderer reads optionNames by index, so a length mismatch mislabels."""
    assert len(branch["enumNames"]) == len(branch["enum"]), (component, field)


# --------------------------------------------------------------------------- #
# What must keep showing its raw value
# --------------------------------------------------------------------------- #


def test_model_checkpoints_are_left_alone():
    """The identifier is what a user wants to see; renaming it loses information."""
    for component, field, branch in BRANCHES:
        if any("/" in option for option in branch["enum"]):
            assert "enumNames" not in branch, (component, field)


def test_device_lists_are_left_alone():
    """One of them is built at import time from the machine's own GPU name."""
    for component, field, branch in BRANCHES:
        if set(branch["enum"]) & {"GPU", "CPU", "cpu", "cuda"}:
            assert "enumNames" not in branch, (component, field)


# --------------------------------------------------------------------------- #
# Coverage, as a number that can move
# --------------------------------------------------------------------------- #


def test_coverage_is_tracked():
    """Not a target, a tripwire.

    The floor catches a regression that silently drops the table; the ceiling
    catches labels being added to the two families that must not have them,
    which the two tests above would also catch but less legibly.
    """
    labelled = [b for _, _, b in BRANCHES if b.get("enumNames")]
    assert len(BRANCHES) > 200
    assert 60 <= len(labelled) <= 140, (len(labelled), len(BRANCHES))
