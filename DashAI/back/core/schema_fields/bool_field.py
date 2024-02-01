from pydantic import Field
from typing_extensions import Annotated


def bool_field(
    description: str,
    default: bool,
):
    """Function to create a pydantic-like boolean type.

    Parameters
    ----------
    description: str
        Description of the field.
    default: bool
        The default value to show to the user.

    Returns
    -------
    type[bool]
        A pydantic-like type to represent the boolean.
    """
    return Annotated[
        bool,
        Field(description=description, default=default),
    ]
