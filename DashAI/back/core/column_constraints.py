"""Type, dtype and cardinality checks shared by explorers and converters."""

from typing import Any, Dict, List


def columns_satisfy_metadata(
    metadata: Dict[str, Any],
    column_names: List[str],
    columns_spec: Dict[str, Dict[str, Any]],
) -> bool:
    """Check selected columns against a component's declared restrictions.

    The same rule the frontend applies in ``columnEligibility.js``: an empty
    ``allowed_types`` or ``allowed_dtypes`` means no restriction, the
    ``non_allowed_dtypes`` blacklist always applies, and the number of
    selected columns must satisfy ``input_cardinality``. A document exposes
    one column per content type, so the same check covers document items.

    Parameters
    ----------
    metadata : Dict[str, Any]
        The component metadata as returned by ``get_metadata``.
    column_names : List[str]
        The selected column names, or content type names for a document.
    columns_spec : Dict[str, Dict[str, Any]]
        Column name to a dict with at least ``"type"`` and ``"dtype"``.

    Returns
    -------
    bool
        True when every restriction is satisfied.
    """
    allowed_types = metadata.get("allowed_types", [])
    allowed_dtypes = metadata.get("allowed_dtypes", [])
    non_allowed_dtypes = metadata.get("non_allowed_dtypes", [])
    cardinality = metadata.get("input_cardinality") or {}

    n = len(column_names)
    if "exact" in cardinality and n != cardinality["exact"]:
        return False
    if "min" in cardinality and n < cardinality["min"]:
        return False
    if "max" in cardinality and n > cardinality["max"]:
        return False

    for column_name in column_names:
        column_info = columns_spec.get(column_name, {})
        column_type = column_info.get("type", "")
        column_dtype = column_info.get("dtype", "")
        if allowed_types and column_type not in allowed_types:
            return False
        if non_allowed_dtypes and column_dtype in non_allowed_dtypes:
            return False
        if allowed_dtypes and column_dtype not in allowed_dtypes:
            return False
    return True
