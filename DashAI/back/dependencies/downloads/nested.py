"""Discover nested downloadable components inside a parameters dict.

A DashAI component may take another component as a parameter (a
``component_field``). That child may itself require a download, and the child
may in turn nest further components. This module walks a parameters dict the
same way :class:`~DashAI.back.models.model_factory.ModelFactory` does when it
instantiates the model graph, so the set of components it reports matches the
set that would actually be built.

Two value shapes are handled, mirroring ``ModelFactory._process_param``:

* the canonical ``{"component": <name>, "params": {...}}`` descriptor, and
* the frontend-wrapped ``{"properties": {"component": ..., "params": ...}}``.
"""

from typing import Any, Dict, Iterator, List, Optional, Tuple


def _unwrap(value: Any) -> Any:
    """Strip the single-key ``properties`` wrapper the frontend adds.

    Parameters
    ----------
    value : Any
        A parameter value as stored in a parameters dict.

    Returns
    -------
    Any
        ``value["properties"]`` when ``value`` is a ``{"properties": ...}``
        wrapper, otherwise ``value`` unchanged.
    """
    if isinstance(value, dict) and "properties" in value and len(value) == 1:
        return value["properties"]
    return value


def _iter_value(
    value: Any, parent: Optional[str]
) -> Iterator[Tuple[str, Optional[str]]]:
    """Yield ``(component_name, parent_name)`` for a single parameter value.

    Recurses into the selected component's own parameters so components nested
    at any depth are reported.

    Parameters
    ----------
    value : Any
        A parameter value, possibly a nested component descriptor.
    parent : str or None
        Name of the component that owns this value, used as the ``parent`` of
        any component found directly inside it.

    Yields
    ------
    tuple of (str, str or None)
        The nested component name and the name of its enclosing component.
    """
    value = _unwrap(value)
    if not (isinstance(value, dict) and "component" in value):
        return

    parent_component_name = value["component"]
    inner = value.get("params", {}).get("comp", {})
    if inner == {}:
        name = parent_component_name
        params = value.get("params", {})
    else:
        name = inner.get("component")
        params = inner.get("params", {})

    if name:
        yield name, parent
    if isinstance(params, dict):
        for sub_value in params.values():
            yield from _iter_value(sub_value, name)


def iter_config_components(
    parameters: Dict[str, Any],
) -> Iterator[Tuple[str, Optional[str]]]:
    """Yield ``(component_name, parent_name)`` for every nested component.

    Parameters
    ----------
    parameters : dict
        A parameters dict as produced by the DashAI configuration UI.

    Yields
    ------
    tuple of (str, str or None)
        Each nested component name paired with its enclosing component name
        (``None`` at the top level).
    """
    for value in parameters.values():
        yield from _iter_value(value, None)


def missing_downloads(
    parameters: Dict[str, Any],
    component_registry,
) -> List[Dict[str, Any]]:
    """Return metadata for nested components that still need downloading.

    Each candidate is reconciled against the filesystem via
    ``refresh_download_status`` so a component downloaded after startup (in the
    worker process) is recognised without an API restart.

    Parameters
    ----------
    parameters : dict
        A parameters dict as produced by the DashAI configuration UI.
    component_registry : ComponentRegistry
        The registry used to resolve component classes and download state.

    Returns
    -------
    list of dict
        One entry per not-yet-downloaded nested component, each with
        ``name``, ``parent``, and ``download_size_bytes`` keys. Empty when
        every nested download-required component is already present.
    """
    missing: List[Dict[str, Any]] = []
    seen = set()
    for name, parent in iter_config_components(parameters):
        if name in seen or name not in component_registry:
            continue
        seen.add(name)
        component_class = component_registry[name]["class"]
        if not getattr(component_class, "REQUIRES_DOWNLOAD", False):
            continue
        if component_registry.refresh_download_status(name):
            continue
        missing.append(
            {
                "name": name,
                "parent": parent,
                "download_size_bytes": getattr(
                    component_class, "DOWNLOAD_SIZE_BYTES", None
                ),
            }
        )
    return missing
