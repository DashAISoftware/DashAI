from typing import List

from pydantic import AfterValidator, Field
from typing_extensions import Annotated


def __check_choices(enum: List[str]):
    """Factory to create custom validator for string field.
    Checks if the input str is in the enum.

    Parameters
    ----------
    enum: List[str]
        All the posible string values of the param.

    Returns
    -------
    str -> str
        A function that inspect the input string.
    """

    def check_str_in_enum(x: str) -> str:
        assert x in enum, f"{x}  is not in the enum"
        return x

    return check_str_in_enum


def string_field(
    description: str,
    default: str,
    enum: List[str],
):
    """Function to create a pydantic-like string type.

    Parameters
    ----------
    description: str
        Description of the field.
    default: str
        The default value to show to the user.
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
            default=default,
            description=description,
            json_schema_extra={
                "enum": enum,
            },
        ),
        AfterValidator(__check_choices(enum)),
    ]
