from kink import inject

from DashAI.back.core.schema_fields.base_schema import BaseSchema
from DashAI.back.dependencies.registry import ComponentRegistry


@inject
def fill_objects(
    schema_instance: BaseSchema,
    component_registry: ComponentRegistry = lambda di: di["component_registry"],
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
