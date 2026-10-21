import pytest

from DashAI.back.dataloaders.classes.document_elements import (
    ELEMENT_KINDS,
    default_kind,
    validate_element,
)
from DashAI.back.types.dashai_image import DashAIImage
from DashAI.back.types.value_types import Text


def test_starting_set_of_kinds():
    assert set(ELEMENT_KINDS) == {
        "title",
        "heading",
        "paragraph",
        "list_item",
        "table",
        "code",
        "quote",
        "caption",
        "image",
        "page_header",
        "page_footer",
        "chunk",
    }


def test_defaults_per_type():
    assert default_kind(Text) == "paragraph"
    assert default_kind(DashAIImage) == "image"


def test_attrs_get_their_defaults():
    assert validate_element("paragraph", Text, None) == {}
    assert validate_element("list_item", Text, {}) == {"ordered": False, "depth": 0}
    assert validate_element("table", Text, {"rows": [["a", "b"]]}) == {
        "rows": [["a", "b"]],
        "header": False,
    }
    assert validate_element("heading", Text, {"level": 2}) == {"level": 2}
    assert validate_element("code", Text, {"language": "json"}) == {"language": "json"}
    assert validate_element("image", DashAIImage, {"alt": "Figure 1"}) == {
        "alt": "Figure 1"
    }


def test_unknown_kind_is_rejected():
    with pytest.raises(ValueError, match="Unknown element kind"):
        validate_element("sidebar", Text, {})


def test_kind_must_match_the_dashai_type():
    with pytest.raises(ValueError, match="holds Image"):
        validate_element("image", Text, {})
    with pytest.raises(ValueError, match="holds Text"):
        validate_element("heading", DashAIImage, {"level": 1})


@pytest.mark.parametrize(
    ("kind", "attrs"),
    [
        ("heading", {}),
        ("heading", {"level": 0}),
        ("heading", {"level": 7}),
        ("heading", {"level": True}),
        ("list_item", {"depth": -1}),
        ("list_item", {"ordered": "yes"}),
        ("table", {}),
        ("table", {"rows": "a\tb"}),
        ("table", {"rows": [["a", 1]]}),
        ("code", {"language": 3}),
        ("paragraph", {"level": 1}),
    ],
)
def test_invalid_attrs_are_rejected(kind, attrs):
    with pytest.raises(ValueError, match="must be|requires|does not take"):
        validate_element(kind, Text, attrs)
