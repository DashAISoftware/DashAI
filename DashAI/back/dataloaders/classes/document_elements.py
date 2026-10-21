"""Structural element kinds of a DashAIDocument and their attributes."""

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from DashAI.back.types.dashai_image import DashAIImage
from DashAI.back.types.value_types import Text


def _is_int(value: Any) -> bool:
    """Tell whether a value is an int and not a bool."""
    return isinstance(value, int) and not isinstance(value, bool)


def _is_rows(value: Any) -> bool:
    """Tell whether a value is a list of rows of string cells."""
    return isinstance(value, list) and all(
        isinstance(row, list) and all(isinstance(cell, str) for cell in row)
        for row in value
    )


def _is_page_pair(value: Any) -> bool:
    """Return whether a value is a ``[first, last]`` pair of pages or nulls.

    Parameters
    ----------
    value : Any
        The attribute value.

    Returns
    -------
    bool
        True for a two item list of 1-based page numbers or None.
    """
    return (
        isinstance(value, list)
        and len(value) == 2
        and all(page is None or (_is_int(page) and page >= 1) for page in value)
    )


def _is_positions(value: Any) -> bool:
    """Return whether a value is a list of item positions.

    Parameters
    ----------
    value : Any
        The attribute value.

    Returns
    -------
    bool
        True for a list of ints >= 0.
    """
    return isinstance(value, list) and all(
        _is_int(position) and position >= 0 for position in value
    )


@dataclass(frozen=True)
class AttrSpec:
    """Rule for one attribute of an element kind.

    Parameters
    ----------
    check : Callable[[Any], bool]
        Returns True when a value is valid.
    description : str
        What a valid value looks like, used in error messages.
    required : bool
        Whether the attribute must be given.
    default : Any
        Value used when an optional attribute is missing; ``None`` leaves
        it out.
    """

    check: Callable[[Any], bool]
    description: str
    required: bool = False
    default: Any = None


@dataclass(frozen=True)
class ElementKind:
    """Definition of one structural element kind.

    Parameters
    ----------
    content_type : type
        DashAI type the element content must have.
    attrs : Dict[str, AttrSpec]
        Allowed attributes.
    """

    content_type: type
    attrs: Dict[str, AttrSpec] = field(default_factory=dict)


ELEMENT_KINDS: Dict[str, ElementKind] = {
    "title": ElementKind(Text),
    "heading": ElementKind(
        Text,
        {
            "level": AttrSpec(
                lambda v: _is_int(v) and 1 <= v <= 6,
                "an int from 1 to 6",
                required=True,
            )
        },
    ),
    "paragraph": ElementKind(Text),
    "list_item": ElementKind(
        Text,
        {
            "ordered": AttrSpec(lambda v: isinstance(v, bool), "a bool", default=False),
            "depth": AttrSpec(
                lambda v: _is_int(v) and v >= 0, "an int >= 0", default=0
            ),
        },
    ),
    "table": ElementKind(
        Text,
        {
            "rows": AttrSpec(_is_rows, "a list of rows of str cells", required=True),
            "header": AttrSpec(lambda v: isinstance(v, bool), "a bool", default=False),
        },
    ),
    "code": ElementKind(
        Text, {"language": AttrSpec(lambda v: isinstance(v, str), "a str")}
    ),
    "quote": ElementKind(Text),
    "caption": ElementKind(Text),
    "image": ElementKind(
        DashAIImage, {"alt": AttrSpec(lambda v: isinstance(v, str), "a str")}
    ),
    "page_header": ElementKind(Text),
    "page_footer": ElementKind(Text),
    "chunk": ElementKind(
        Text,
        {
            "pages": AttrSpec(_is_page_pair, "a [first, last] pair of pages"),
            "sources": AttrSpec(_is_positions, "a list of item positions", default=[]),
        },
    ),
}

DEFAULT_KINDS: Dict[type, str] = {Text: "paragraph", DashAIImage: "image"}

TABLE_KIND = "table"
CHUNK_KIND = "chunk"


def table_text(rows: List[List[str]]) -> str:
    """Render the rows of a table item as its text content.

    Parameters
    ----------
    rows : List[List[str]]
        Rows of string cells, as stored in the ``rows`` attribute.

    Returns
    -------
    str
        Newline separated rows of tab separated cells.
    """
    return "\n".join("\t".join(row) for row in rows)


def default_kind(content_type: type) -> str:
    """Return the kind used when an item does not name one.

    Parameters
    ----------
    content_type : type
        ``Text`` or ``DashAIImage``.

    Returns
    -------
    str
        ``"paragraph"`` for Text, ``"image"`` for images.
    """
    return DEFAULT_KINDS[content_type]


def validate_element(
    kind: str, content_type: type, attrs: Optional[Dict[str, Any]]
) -> Dict[str, Any]:
    """Check an element kind against its content type and attributes.

    Parameters
    ----------
    kind : str
        Element kind name.
    content_type : type
        DashAI type of the item content.
    attrs : Optional[Dict[str, Any]]
        Element attributes.

    Returns
    -------
    Dict[str, Any]
        The attributes with defaults filled in.

    Raises
    ------
    ValueError
        If the kind is unknown, does not hold ``content_type``, or the
        attributes are unknown, missing or of the wrong type.
    """
    spec = ELEMENT_KINDS.get(kind)
    if spec is None:
        raise ValueError(
            f"Unknown element kind {kind!r}; known: {', '.join(ELEMENT_KINDS)}."
        )
    if spec.content_type is not content_type:
        raise ValueError(
            f"Element kind {kind!r} holds {spec.content_type.display_name()}, "
            f"not {content_type.display_name()}."
        )
    given = dict(attrs or {})
    unknown = sorted(set(given) - set(spec.attrs))
    if unknown:
        raise ValueError(f"Element kind {kind!r} does not take attributes {unknown}.")
    result = {}
    for name, rule in spec.attrs.items():
        if name not in given:
            if rule.required:
                raise ValueError(f"Element kind {kind!r} requires attribute {name!r}.")
            if rule.default is not None:
                result[name] = rule.default
            continue
        if not rule.check(given[name]):
            raise ValueError(
                f"Attribute {name!r} of {kind!r} must be {rule.description}, "
                f"got {given[name]!r}."
            )
        result[name] = given[name]
    return result
