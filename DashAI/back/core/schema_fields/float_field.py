from typing import Optional

from pydantic import Field
from typing_extensions import Annotated


def float_field(
    description: str,
    default: float,
    minimum: Optional[float] = None,
    exclusive_minimum: Optional[float] = None,
    maximum: Optional[float] = None,
):
    """Function to create a pydantic-like float type.

    Parameters
    ----------
    description: str
        Description of the field.
    default: float
        The default value to show to the user.
    minimum: Optional float
        Minimum value of the field.
    exclusive_minimum: Optional float
        Exclusive minimum value of the field.
    maximum: Optional float
        Maximum value of the field.

    Returns
    -------
    type[float]
        A pydantic-like type to represent the float.

    Raises
    ------
    ValidationError
        If the value of the field is less than the minimum.
    ValidationError
        If the value of the field is less or equal than the exclusive minimum.
    ValidationError
        If the value of the field is greater than the maximum.
    """
    params = {"description": description, "default": default}
    if minimum:
        params["ge"] = minimum
    if exclusive_minimum:
        params["gt"] = exclusive_minimum
    if maximum:
        params["le"] = maximum
    return Annotated[
        float,
        Field(**params),
    ]
