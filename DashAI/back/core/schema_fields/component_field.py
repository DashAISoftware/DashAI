from typing import Type

from pydantic import BaseModel, Field
from typing_extensions import Annotated


class ComponentType(BaseModel):
    component: str
    params: dict


def component_field(parent: str) -> Type[ComponentType]:
    """Function to create a custom pydantic-like type to support components.

    Parameters
    ----------
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
        Field(json_schema_extra={"parent": parent}),
    ]
