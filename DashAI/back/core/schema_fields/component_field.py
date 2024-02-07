from pydantic import BaseModel, Field
from typing_extensions import Annotated


class ComponentType(BaseModel):
    component: str
    params: dict


def component_field(
    description: str,
    parent: str,
):
    """Function to create a custom pydantic-like type to support components.

    Parameters
    ----------
    description: str
        Description of the field.
    parent: str
        The name of the parent class of the component.
        Is used to select the components to show to the user.

    Returns
    -------
    type[ComponentType]
        A pydantic-like type to represent the component.
    """
    return Annotated[
        ComponentType,
        Field(
            description=description,
            json_schema_extra={"parent": parent},
        ),
    ]
