from typing import Type, TypeVar

from pydantic import Field
from typing_extensions import Annotated

T = TypeVar("T")


def schema_field(t: T, placeholder: T, description: str) -> Type[T]:
    """Function to create a schema field of type T.

    Parameters
    ----------
    description: str
        A string that describes the field.
    placeholder: T
        The value that will be displayed to the user.

    Returns
    -------
    type[T]
        A pydantic-like type to represent the schema field.
    """
    return Annotated[
        t,
        Field(description=description, json_schema_extra={"placeholder": placeholder}),
    ]
