from typing import Any, Optional, Type

from pydantic import BaseModel, Field, GetCoreSchemaHandler
from pydantic_core import core_schema
from typing_extensions import Annotated


class OptimizableIntField(BaseModel):
    optimize: bool
    fixed_value: int
    lower_bound: int
    upper_bound: int

    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: Any, handler: GetCoreSchemaHandler
    ) -> core_schema.CoreSchema:
        return core_schema.typed_dict_schema(
            {
                "optimize": core_schema.typed_dict_field(core_schema.bool_schema()),
                "fixed_value": core_schema.typed_dict_field(core_schema.int_schema()),
                "lower_bound": core_schema.typed_dict_field(core_schema.int_schema()),
                "upper_bound": core_schema.typed_dict_field(core_schema.int_schema()),
            },
        )


def optimizer_int_field(
    ge: Optional[int] = None,
    gt: Optional[int] = None,
    le: Optional[int] = None,
    lt: Optional[int] = None,
) -> Type[OptimizableIntField]:
    """Function to create a pydantic-like optimizable integer type.

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
    type[OptimizableIntField]
        A pydantic-like type to represent an optimizable integer.
    """
    return Annotated[
        OptimizableIntField,
        Field(),
    ]
