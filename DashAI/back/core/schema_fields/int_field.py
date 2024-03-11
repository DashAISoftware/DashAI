from typing import Optional

from pydantic import Field
from typing_extensions import Annotated


def int_field(
    description: str,
    placeholder: int,
    ge: Optional[int] = None,
    gt: Optional[int] = None,
    le: Optional[int] = None,
    lt: Optional[int] = None,
):
    """Function to create a pydantic-like integer type.

    Parameters
    ----------
    description: str
        A string that describes the field.
    placeholder: int
        The integer value that will be displayed to the user.
    ge: Optional[int]
        An optional integer that the value should be greater than or equal to.
        If not provided, there is no lower limit.
    gt: Optional[int]
        An optional integer that the value should be strictly greater than.
        If not provided, there is no strict lower limit.
    le: Optional[int]
        An optional integer that the value should be less than or equal to.
        If not provided, there is no upper limit.
    lt: Optional[int]
        An optional integer that the value should be strictly less than.
        If not provided, there is no strict upper limit.

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
    return Annotated[
        int,
        Field(
            description=description,
            ge=ge,
            gt=gt,
            le=le,
            lt=lt,
            json_schema_extra={"placeholder": placeholder},
        ),
    ]
