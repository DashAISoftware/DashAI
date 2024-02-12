from typing import Callable, List, Type

from pydantic import AfterValidator, Field
from typing_extensions import Annotated


def __check_choices(enum: List[str]) -> Callable[[str], str]:
    """Factory to create custom validator for string field.
    Checks if the input str is in the enum.

    Parameters
    ----------
    enum: List[str]
        All the posible string values of the param.

    Returns
    -------
    Callable[str, str]
        A function that checks if the string is within the possible values specified
        in the enum.
    """

    def check_str_in_enum(x: str) -> str:
        if x not in enum:
            raise ValueError(f"{x} is not in the enum")
        return x

    return check_str_in_enum


def string_field(enum: List[str]) -> Type[str]:
    """Function to create a pydantic-like string type.

    Parameters
    ----------
    enum: List[str]
        All the posible string values of the field.

    Returns
    -------
    type[str]
        A pydantic-like type to represent the string.

    Raises
    ------
    ValidationError
        If the value of the field is not in the enum list.
    """
    return Annotated[
        str,
        Field(
            validate_default=True,
            json_schema_extra={"enum": enum},
        ),
        AfterValidator(__check_choices(enum)),
    ]
