"""Resolution of component defaults from their schema placeholders.

``schema_field`` never sets a pydantic ``default``: every field of every
component schema is required, and ``placeholder`` is only a UI hint carried in
``json_schema_extra``.  This module is the single place that turns those
placeholders into a real params dict, so the backend can hand out complete,
ready-to-persist configurations instead of expecting the client to assemble
them.
"""

from typing import Any, Dict

__all__ = ["resolve_component_defaults"]


def resolve_component_defaults(component_name: str, registry) -> Dict[str, Any]:
    """Resolve a component's schema placeholders into a params dict.

    Recursively resolves nested component placeholders of the form
    ``{"component": ..., "params": {}}`` into
    ``{"component": ..., "params": {...}}``.  Unregistered components resolve
    to an empty dict so a stale placeholder cannot crash the caller.

    Parameters
    ----------
    component_name : str
        Name of the component whose defaults are wanted.
    registry : ComponentRegistry
        Registry used to look up the component schema.

    Returns
    -------
    dict
        The resolved parameters for ``component_name``.
    """
    if component_name not in registry:
        return {}
    schema = registry[component_name]["schema"] or {}
    params: Dict[str, Any] = {}
    for key, prop in schema.get("properties", {}).items():
        placeholder = prop.get("placeholder")
        if isinstance(placeholder, dict) and "component" in placeholder:
            params[key] = {
                "component": placeholder["component"],
                "params": {
                    **resolve_component_defaults(placeholder["component"], registry),
                    **placeholder.get("params", {}),
                },
            }
        else:
            params[key] = placeholder
    return params
