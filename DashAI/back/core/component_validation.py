"""Generic component reference validation.

Recursively walks a parameters dict to find all ``{component, params}``
references and validates them against the component registry.

Works for any task (RAG, generative, etc.) — any parameter structure
that uses ``component_field`` produces the ``{component, params}`` pattern.
"""

from typing import Any

from DashAI.back.dependencies.registry.component_registry import ComponentRegistry


def find_component_refs(
    data: Any, path: str = ""
) -> list[tuple[str, str, dict[str, Any]]]:
    """Recursively find all component references in a parameters structure.

    A component reference is any ``dict`` that has both ``"component"`` (``str``)
    and ``"params"`` (``dict``) keys.  Returns a list of
    ``(json_path, component_name, params)`` tuples.

    Parameters
    ----------
    data : Any
        The parameters structure to search (typically a ``dict`` or ``list``).
    path : str
        Dot-separated JSON path for error reporting (used internally during recursion).

    Returns
    -------
    list[tuple[str, str, dict[str, Any]]]
        Each entry: ``("prompt", "DefaultRAGGenerationPrompt", {...})``,
        ``("chunking_model", "CharacterChunkModel", {...})``, etc.
    """
    refs: list[tuple[str, str, dict[str, Any]]] = []
    if isinstance(data, dict):
        if (
            "component" in data
            and "params" in data
            and isinstance(data["component"], str)
            and isinstance(data["params"], dict)
        ):
            refs.append((path, data["component"], data["params"]))
        for key, value in data.items():
            child_path = f"{path}.{key}" if path else key
            refs.extend(find_component_refs(value, child_path))
    elif isinstance(data, list):
        for i, item in enumerate(data):
            refs.extend(find_component_refs(item, f"{path}[{i}]"))
    return refs


def validate_component_refs(data: Any, registry: ComponentRegistry) -> list[str]:
    """Validate that all component references exist in the registry.

    Walks ``data`` recursively via :func:`find_component_refs` and checks
    each component name against ``registry``.

    Parameters
    ----------
    data : Any
        Parameters structure to validate.
    registry : ComponentRegistry
        The application's component registry.

    Returns
    -------
    list[str]
        Error messages (empty list means all references are valid).
        Each message like ``"'NonExistent' at 'chunking_model' not registered."``
    """
    errors: list[str] = []
    for path, name, _params in find_component_refs(data):
        if name not in registry:
            errors.append(f"Component '{name}' at '{path}' is not registered.")
    return errors
