"""The kinds of data a converter or explorer can run on.

Converters and explorers declare ``data_kinds`` in their class ``metadata``.
A component that declares nothing runs on datasets only, which keeps every
existing component and plugin where it was before documents existed.
"""

from typing import Any, Dict, Iterable, List, Optional

DATASET = "dataset"
DOCUMENT = "document"
DATA_KINDS = (DATASET, DOCUMENT)
DEFAULT_DATA_KINDS = (DATASET,)


def normalize_data_kinds(raw: Any) -> List[str]:
    """Turn a declared ``data_kinds`` value into a list of known kinds.

    Parameters
    ----------
    raw : Any
        The declared value: None, a single kind string, or an iterable of
        kind strings.

    Returns
    -------
    List[str]
        The declared kinds without duplicates, in declaration order, or
        ``["dataset"]`` when nothing was declared.

    Raises
    ------
    ValueError
        If a declared kind is not one of ``DATA_KINDS``.
    """
    if raw is None:
        return list(DEFAULT_DATA_KINDS)
    if isinstance(raw, str):
        raw = [raw]
    kinds: List[str] = []
    for kind in raw:
        if kind not in DATA_KINDS:
            raise ValueError(
                f"Unknown data kind {kind!r}; expected one of {list(DATA_KINDS)}."
            )
        if kind not in kinds:
            kinds.append(kind)
    return kinds or list(DEFAULT_DATA_KINDS)


def component_data_kinds(component_class: type) -> List[str]:
    """Return the data kinds a component class declares.

    Parameters
    ----------
    component_class : type
        A converter or explorer class.

    Returns
    -------
    List[str]
        The normalized kinds read from the class ``metadata`` dict.
    """
    metadata = getattr(component_class, "metadata", None) or {}
    return normalize_data_kinds(metadata.get("data_kinds"))


def supports_data_kind(component_class: type, kind: str) -> bool:
    """Tell whether a component class runs on the given data kind.

    Parameters
    ----------
    component_class : type
        A converter or explorer class.
    kind : str
        ``"dataset"`` or ``"document"``.

    Returns
    -------
    bool
        True when the class declares the kind.
    """
    return kind in component_data_kinds(component_class)


def type_names(raw_types: Iterable[Any]) -> List[str]:
    """Serialize DashAI type classes to the names columns report.

    Parameters
    ----------
    raw_types : Iterable[Any]
        DashAI type classes, or names already serialized.

    Returns
    -------
    List[str]
        The display name of each type.
    """
    return [
        value.display_name()
        if hasattr(value, "display_name")
        else getattr(value, "__name__", value)
        for value in raw_types
    ]


def document_type_error(
    metadata: Dict[str, Any], selected_types: Iterable[str]
) -> Optional[str]:
    """Check selected content types against a tool's document type limit.

    A tool may declare ``document_allowed_types`` to accept fewer content
    types on documents than its ``allowed_types`` accept on datasets, such
    as an explorer that takes any column but only Text items.

    Parameters
    ----------
    metadata : Dict[str, Any]
        The tool metadata from ``get_metadata``.
    selected_types : Iterable[str]
        The selected content type names.

    Returns
    -------
    Optional[str]
        A message naming the refused types, or None when all are accepted.
    """
    allowed = metadata.get("document_allowed_types")
    if not allowed:
        return None
    refused = [name for name in selected_types if name not in allowed]
    if not refused:
        return None
    return (
        f"This tool runs on {', '.join(allowed)} items of a document, not "
        f"{', '.join(refused)}."
    )
