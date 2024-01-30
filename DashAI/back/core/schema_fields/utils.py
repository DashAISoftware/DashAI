from dependency_injector.wiring import Provide, inject

from DashAI.back.core.schema_fields.base_schema import BaseSchema
from DashAI.back.core.schema_fields.object_field import ComponentType


@inject
def fill_objects(
    schema_instance: BaseSchema,
    component_registry=Provide["component_registry"],
) -> BaseSchema:
    """Fills in the schema instance, replacing the component fields with the
    target component.

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
    BaseSchema
        The instance of the schema with the components filled in.
    """
    for field_name, field_value in iter(schema_instance):
        if isinstance(field_value, ComponentType):
            component_class = component_registry[field_value.component]["class"]
            validated_params = component_class.SCHEMA.model_validate(field_value.params)
            complete_params = fill_objects(validated_params)
            setattr(
                schema_instance,
                field_name,
                component_class(**complete_params.model_dump()),
            )
    return schema_instance
