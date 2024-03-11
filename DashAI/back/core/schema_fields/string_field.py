from typing import Callable, List, Type

from pydantic import AfterValidator, GetJsonSchemaHandler
from pydantic.json_schema import JsonSchemaValue
from pydantic_core import core_schema
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


class StringField:
    pass


def _field_string_factory(enum: List[str]) -> Type[StringField]:
    """Factory function to create a StringField parameterized by
    the component parent.
    It overwrites the schema of the model in order to show the enum field.
    Parameters
    ----------
    enum: List[str]
        All the posible string values of the field.
    Returns
    -------
    type[StringField]
        A pydantic-like type to represent a string.
    """

    class StringFieldWithEnum(StringField):
        @classmethod
        def __get_pydantic_json_schema__(
            cls, core_schema: core_schema.CoreSchema, handler: GetJsonSchemaHandler
        ) -> JsonSchemaValue:
            json_schema = handler(core_schema)
            json_schema = handler.resolve_ref_schema(json_schema)
            json_schema["enum"] = enum
            return json_schema

    return StringFieldWithEnum


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
        _field_string_factory(enum),
        AfterValidator(__check_choices(enum)),
    ]
