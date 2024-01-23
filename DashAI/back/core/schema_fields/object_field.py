from pydantic import BaseModel, Field
from typing_extensions import Annotated


class ComponentType(BaseModel):
    component: str
    params: dict


def component_field(
    description: str,
    default: dict,
    parent: str,
):
    return Annotated[
        ComponentType,
        Field(
            description=description,
            default=default,
            json_schema_extra={"parent": parent},
        ),
    ]
