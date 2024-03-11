from typing import Optional

from pydantic import Field
from typing_extensions import Annotated


def float_field(
    description: str,
    placeholder: float,
    ge: Optional[float] = None,
    gt: Optional[float] = None,
    le: Optional[float] = None,
    lt: Optional[float] = None,
):
    """Function to create a pydantic-like float type.

    Parameters
    ----------
    description: str
        A string that describes the field.
    placeholder: float
        The float value that will be displayed to the user.
    ge: Optional[float]
        An optional float that the value should be greater than or equal to.
        If not provided, there is no lower limit.
    gt: Optional[float]
        An optional float that the value should be strictly greater than.
        If not provided, there is no strict lower limit.
    le: Optional[float]
        An optional float that the value should be less than or equal to.
        If not provided, there is no upper limit.
    lt: Optional[float]
        An optional float that the value should be strictly less than.
        If not provided, there is no strict upper limit.

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
    return Annotated[
        float,
        Field(
            description=description,
            ge=ge,
            gt=gt,
            le=le,
            lt=lt,
            json_schema_extra={"placeholder": placeholder},
        ),
    ]
