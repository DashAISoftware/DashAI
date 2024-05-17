from typing import Optional, Type

from pydantic import Field
from typing_extensions import Annotated


def optimizer_int_field(
    ge: Optional[int] = None,
    gt: Optional[int] = None,
    le: Optional[int] = None,
    lt: Optional[int] = None,
) -> Type[int]:
    """Function to create a pydantic-like integer type.

    Parameters
    ----------
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
        If the value of the field is less or equal than the exclusive minimum.
    ValidationError
        If the value of the field is greater than the maximum.
    ValidationError
        If the value of the field is greater or equal than the exclusive maximum.
    """
    return dict
