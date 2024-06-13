from typing import Any, Callable, Optional, Type

from pydantic import AfterValidator, BaseModel, Field, GetCoreSchemaHandler
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


def __check_order_factory(
    ge: Optional[int] = None,
    gt: Optional[int] = None,
    le: Optional[int] = None,
    lt: Optional[int] = None,
) -> Callable[[OptimizableIntField], OptimizableIntField]:
    """Factory to create custom validator for Optimize integer field.
    Checks if the input meets the order restrictions.

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
    Callable[OptimizableIntField, OptimizableIntField]
        A function that checks if the input meets the order restrictions.
    """

    def check_order(x: OptimizableIntField) -> OptimizableIntField:
        if ge is not None and (
            x["fixed_value"] < ge or x["lower_bound"] < ge or x["upper_bound"] < ge
        ):
            raise ValueError(f"Input should be greater than or equal {ge}")
        if gt is not None and (
            x["fixed_value"] <= gt or x["lower_bound"] <= gt or x["upper_bound"] <= gt
        ):
            raise ValueError(f"Input should be greater than {gt}")
        if le is not None and (
            x["fixed_value"] > le or x["lower_bound"] > le or x["upper_bound"] > le
        ):
            raise ValueError(f"Input should be less than or equal {le}")
        if lt is not None and (
            x["fixed_value"] >= lt or x["lower_bound"] >= le or x["upper_bound"] >= le
        ):
            raise ValueError(f"Input should be less than {le}")
        return x

    return check_order


def __check_bound_order(x: OptimizableIntField) -> OptimizableIntField:
    if x["lower_bound"] > x["upper_bound"]:
        raise ValueError("lower_bound must be less or equal than upper_bound")
    return x


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
        AfterValidator(__check_order_factory(ge, gt, le, lt)),
        AfterValidator(__check_bound_order),
    ]
