"""Helpers for the ``{component, params}`` reference shape used by RAG configs."""

from __future__ import annotations

from typing import Any


def is_component_ref(value: Any) -> bool:
    """Return whether ``value`` is a ``{component, params}`` reference dict.

    Parameters
    ----------
    value : Any
        Candidate configuration value.

    Returns
    -------
    bool
        ``True`` when ``value`` is a dict carrying a string ``component`` and a
        ``params`` entry.
    """
    return (
        isinstance(value, dict)
        and "component" in value
        and "params" in value
        and isinstance(value.get("component"), str)
    )
