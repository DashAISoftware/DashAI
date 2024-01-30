from pydantic import AfterValidator, BaseModel, Field
from typing_extensions import Annotated


class ComponentType(BaseModel):
    component: str
    params: dict


def __check_component(parent: str):
    """Factory to create custom validator for component field.
    Checks if the component is in the registry and
    if the component is subclass of the parent component.

    Parameters
    ----------
    parent: str
        The name of the parent class of the component.

    Returns
    -------
    ComponentType -> ComponentType
        A function that inspects the input component.
    """

    def check_component_in_registry(component: ComponentType):
        # Check if component in registry.
        # Check component is subclass of parent
        return component

    return check_component_in_registry


def component_field(
    description: str,
    default: str,
    parent: str,
):
    """Function to create a custom pydantic-like type to support components.

    Parameters
    ----------
    description: str
        Description of the field.
    default: str
        The default value to show to the user.
    parent: str
        The name of the parent class of the component.
        Is used to select the components to show to the user.

    Returns
    -------
    type[ComponentType]
        A pydantic-like type to represent the component.

    Raises
    ------
    ValidationError
        If the component name of the field is not in the registry.
    ValidationError
        If the component name of the field is not a subclass of the parent component.
    """
    return Annotated[
        ComponentType,
        Field(
            description=description,
            default=default,
            json_schema_extra={"parent": parent},
        ),
        AfterValidator(__check_component(parent)),
    ]
