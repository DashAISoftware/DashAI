from typing import Any, Optional, Type

from pydantic import BaseModel, Field, GetCoreSchemaHandler
from pydantic_core import core_schema
from typing_extensions import Annotated


class OptimizableFloatField(BaseModel):
    optimize: bool
    fixed_value: float
    lower_bound: float
    upper_bound: float

    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: Any, handler: GetCoreSchemaHandler
    ) -> core_schema.CoreSchema:
        return core_schema.typed_dict_schema(
            {
                "optimize": core_schema.typed_dict_field(core_schema.bool_schema()),
                "fixed_value": core_schema.typed_dict_field(core_schema.float_schema()),
                "lower_bound": core_schema.typed_dict_field(core_schema.float_schema()),
                "upper_bound": core_schema.typed_dict_field(core_schema.float_schema()),
            },
        )


def optimizer_float_field(
    ge: Optional[int] = None,
    gt: Optional[int] = None,
    le: Optional[int] = None,
    lt: Optional[int] = None,
) -> Type[OptimizableFloatField]:
    """Function to create a pydantic-like optimizable float type.

    Parameters
    ----------
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
    type[OptimizableFloatField]
        A pydantic-like type to represent an optimizable float.
    """
    return Annotated[
        OptimizableFloatField,
        Field(),
    ]
