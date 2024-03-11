from typing import Any, Type

from pydantic import BaseModel, Field, GetCoreSchemaHandler, GetJsonSchemaHandler
from pydantic.json_schema import JsonSchemaValue
from pydantic_core import core_schema
from typing_extensions import Annotated


class ComponentType(BaseModel):
    component: str
    params: dict


def _component_type_factory(parent: str) -> Type[ComponentType]:
    """Factory function to create a ComponentType parameterized by
    the component parent.
    It overwrites the schema of the model in order to show the parent field
    and avoid the $defs definitions.

    Parameters
    ----------
    parent: str
        The name of the parent class of the component.

    Returns
    -------
    type[ComponentType]
        A pydantic-like type to represent the component.
    """

    class ComponentTypeWithParent(ComponentType):
        component: str
        params: dict

        @classmethod
        def __get_pydantic_core_schema__(
            cls, source_type: Any, handler: GetCoreSchemaHandler
        ) -> core_schema.CoreSchema:
            return core_schema.typed_dict_schema(
                {
                    "component": core_schema.typed_dict_field(core_schema.str_schema()),
                    "params": core_schema.typed_dict_field(core_schema.dict_schema()),
                },
            )

        @classmethod
        def __get_pydantic_json_schema__(
            cls, core_schema: core_schema.CoreSchema, handler: GetJsonSchemaHandler
        ) -> JsonSchemaValue:
            json_schema = handler(core_schema)
            json_schema = handler.resolve_ref_schema(json_schema)
            json_schema["parent"] = parent
            return json_schema

    return ComponentTypeWithParent


def component_field(parent: str) -> Type[ComponentType]:
    """Function to create a custom pydantic-like type to support components.

    Parameters
    ----------
    parent: str
        The name of the parent class of the component.
        Is used to select the components to show to the user.

    Returns
    -------
    type[ComponentType]
        A pydantic-like type to represent the component.
    """
    return Annotated[
        _component_type_factory(parent),
        Field(),
    ]
