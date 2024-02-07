from dependency_injector.wiring import Provide, inject

from DashAI.back.core.schema_fields.base_schema import BaseSchema


@inject
def fill_objects(
    schema_instance: BaseSchema,
    component_registry=Provide["component_registry"],
) -> dict:
    """Fills in the schema instance, replacing the component fields with the
    target component. Returns the dumped dictionary of the schema instance.

    This function transforms all fields of the component into actual components.
    To do this, the component type is looked up in the component registry and
    instantiated using the corresponding parameters.

    The function is called recursively on component parameters, to fill its
    internal components.

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
            validated_params = component_class.SCHEMA.model_validate(
                field_value["params"]
            )
            complete_params = fill_objects(validated_params)
            schema_params[field_name] = component_class(**complete_params)
    return schema_params