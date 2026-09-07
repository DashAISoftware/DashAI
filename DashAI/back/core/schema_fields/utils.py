from typing import TYPE_CHECKING

from kink import inject

if TYPE_CHECKING:
    from DashAI.back.core.schema_fields.base_schema import BaseSchema
    from DashAI.back.dependencies.registry import ComponentRegistry


def normalize_payload(data):
    """Recursively normalizes the frontend ``properties`` wrapper into the
    canonical ``{component, params}`` format.

    This is the factored-out version of the unwrapping logic found in
    ``model_factory._process_param`` (approximately line 162).

    The frontend auto-generated forms (``generateInitialValues`` in
    ``utils/schema.js``) produce a ``properties`` wrapper structure:

    .. code-block:: python

        {
            "properties": {
                "component": "ParentModelName",
                "params": {
                    "comp": {
                        "component": "ActualModelName",
                        "params": { ... sub‑params ... },
                    },
                },
            },
        }

    This function converts it into the canonical form that
    ``fill_objects()`` and ``model_class.SCHEMA.model_validate()`` expect:

    .. code-block:: python

        {"component": "ActualModelName", "params": { ... sub‑params ... }}

    Any scalar, list, or already-canonical dict values are returned
    unchanged.

    Parameters
    ----------
    data : Any
        Arbitrary JSON-like data (output of ``model_dump()`` or raw
        frontend payload) that may contain ``properties`` wrappers.

    Returns
    -------
    Any
        The same data with all ``properties`` wrappers replaced by the
        canonical ``{component, params}`` form.
    """
    if isinstance(data, dict):
        if "properties" in data and len(data) == 1:
            inner = data["properties"]
            if isinstance(inner, dict) and "component" in inner:
                raw_params = inner.get("params", {})
                comp = raw_params.get("comp", {})
                if isinstance(comp, dict) and "component" in comp:
                    return {
                        "component": comp["component"],
                        "params": normalize_payload(comp.get("params", {})),
                    }
                return normalize_payload(inner)
        return {k: normalize_payload(v) for k, v in data.items()}
    if isinstance(data, list):
        return [normalize_payload(item) for item in data]
    return data


@inject
def fill_objects(
    schema_instance: "BaseSchema",
    component_registry: "ComponentRegistry" = lambda di: di["component_registry"],
) -> dict:
    """Fills in the schema instance, replacing the component fields with the
    target component. Returns the dumped dictionary of the schema instance.

    This function transforms all fields of the component into actual components.
    To do this, the component type is looked up in the component registry and
    instantiated using the corresponding parameters.

    Example
    ----------
    If the input schema_instance has a dict value:

    ```python
    schema_instance = {
        "dict_field": {"component": "ComponentName", "params": {}},
        "other_field": 1,
    }
    ```
    The function will transform it into:
    ```python
    schema_instance = {"dict_field": ComponentName(), "other_field": 1}
    ```
    Replacing the dictionary with a class instance and not modifying the other fields.

    Parameters
    ----------
    schema_instance : BaseSchema
        An instance of a component schema, constructed using the user's
        parameters.

    Returns
    -------
    dict
        The dictionary representation of the schema instance
        with the components filled in.
    """
    schema_params = schema_instance.model_dump()
    for field_name, field_value in schema_params.items():
        if isinstance(field_value, dict) and {"component", "params"}.issubset(
            set(field_value.keys())
        ):
            component_class = component_registry[field_value["component"]]["class"]
            schema_params[field_name] = component_class(**field_value["params"])
    return schema_params
