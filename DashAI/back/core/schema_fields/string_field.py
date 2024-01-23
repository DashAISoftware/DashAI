from typing import List

from pydantic import AfterValidator, Field
from typing_extensions import Annotated


def check_choices(enum: List[str]):
    def check_str_in_enum(x: str):
        assert x in enum, f"{x}  is not in the enum"
        return x

    return check_str_in_enum


def string_field(
    description: str,
    default: int,
    enum: List[str],
):
    return Annotated[
        str,
        Field(
            default=default,
            description=description,
            json_schema_extra={
                "enum": enum,
            },
        ),
        AfterValidator(check_choices(enum)),
    ]
