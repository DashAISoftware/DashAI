from typing import Optional

from pydantic import Field
from typing_extensions import Annotated


def int_field(
    description: str,
    default: int,
    minimum: Optional[int] = None,
    maximum: Optional[int] = None,
):
    """Function to create a pydantic-like integer type.

    Parameters
    ----------
    description: str
        Description of the field.
    default: int
        The default value to show to the user.
    minimum: Optional int
        Minimum value of the field.
    maximum: Optional int
        Maximum value of the field.

    Returns
    -------
    type[int]
        A pydantic-like type to represent the integer.

    Raises
    ------
    ValidationError
        If the value of the field is less than the minimum.
    ValidationError
        If the value of the field is greater than the maximum.
    """
    params = {"description": description, "default": default, "validate_default": True}
    if minimum:
        params["ge"] = minimum
    if maximum:
        params["le"] = maximum
    return Annotated[
        int,
        Field(**params),
    ]
