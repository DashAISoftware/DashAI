from typing import Any, Callable, Dict, List, Optional, Type

from pydantic import AfterValidator, GetJsonSchemaHandler
from pydantic.json_schema import JsonSchemaValue
from pydantic_core import core_schema
from typing_extensions import Annotated

from DashAI.back.core.schema_fields.enum_labels import labels_for


def __check_choices(enum: List[str]) -> Callable[[str], str]:
    """Factory to create custom validator for enum field.
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


class EnumField:
    pass


def _enum_field_factory(
    enum: List[str], labels: Optional[List[Any]] = None
) -> Type[EnumField]:
    """Factory function to create a EnumField parameterized by
    the enum list.
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

    class EnumFieldWithEnum(EnumField):
        @classmethod
        def __get_pydantic_json_schema__(
            cls, core_schema: core_schema.CoreSchema, handler: GetJsonSchemaHandler
        ) -> JsonSchemaValue:
            json_schema = handler(core_schema)
            json_schema = handler.resolve_ref_schema(json_schema)
            json_schema["enum"] = enum
            if labels is not None:
                json_schema["enumNames"] = labels
            return json_schema

    return EnumFieldWithEnum


def enum_field(enum: List[str], labels: Optional[Dict[str, Any]] = None) -> Type[str]:
    """Function to create a pydantic-like strings enum type.

    Parameters
    ----------
    enum: List[str]
        All the posible string values of the field.
    labels: Optional[Dict[str, Any]]
        What to show the user for an option, keyed by option, as a
        ``MultilingualString`` or a plain string. Emitted as ``enumNames``,
        aligned with ``enum``, which is the key the renderer has always read
        and nothing has ever produced: without it a dropdown displays the raw
        Python value in every language, and an option that is the empty string
        renders as a blank row nobody can identify.

        Options left out of the mapping fall back to their own value, so a
        partial mapping is fine and only the options that need a name get one.

    Returns
    -------
    type[str]
        A pydantic-like type to represent the enum of strings.

    Raises
    ------
    ValidationError
        If the value of the field is not in the enum list.
    """
    if labels is None:
        # Nothing declared: fall back to the shared vocabulary, so a component
        # gets the names for an option set everyone shares without repeating
        # them. Explicit labels always win.
        labels = labels_for(enum) or None

    resolved = None
    if labels is not None:
        unknown = sorted(set(labels) - set(enum))
        if unknown:
            raise ValueError(
                f"enum_field(labels=...) names {unknown}, which are not options "
                f"of this enum ({enum}). A label for an option that does not "
                "exist would never be shown, so it is almost certainly a typo."
            )
        # A list rather than a dict, aligned with `enum`, because the renderer
        # reads it by index.
        resolved = [labels.get(option, option) for option in enum]
    return Annotated[
        str,
        _enum_field_factory(enum, resolved),
        AfterValidator(__check_choices(enum)),
    ]
