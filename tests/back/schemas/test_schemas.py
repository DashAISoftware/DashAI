from abc import ABCMeta
from typing import Final, List, Optional, Union

import pytest
from pydantic import ValidationError

from DashAI.back.config_object import ConfigObject
from DashAI.back.core.schema_fields import (
    BaseSchema,
    bool_field,
    component_field,
    fill_objects,
    float_field,
    int_field,
    string_field,
)
from DashAI.back.dependencies.registry.component_registry import ComponentRegistry


class DummyBaseComponent(ConfigObject, metaclass=ABCMeta):
    """Dummy class representing a component"""

    TYPE: Final[str] = "Component"


class DummyComponent(DummyBaseComponent):
    pass


class DummyBaseConfigComponent(ConfigObject, metaclass=ABCMeta):
    """Dummy base class for configurable components"""

    TYPE: Final[str] = "ConfigComponent"


class DummyParamComponentSchema(BaseSchema):
    comp: component_field(description="", parent="DummyBaseComponent")
    integer: int_field(description="", default=1)


class DummyParamComponent(DummyBaseConfigComponent):
    """A configurable component that has another component as param."""

    SCHEMA = DummyParamComponentSchema

    def __init__(self, **kwargs):
        assert isinstance(kwargs["comp"], DummyBaseComponent)
        assert type(kwargs["integer"]) is int


class NormalSchema(BaseSchema):
    integer: int_field(description="", default=2, le=2, ge=2)
    string: string_field(description="", default="foo", enum=["foo", "bar"])
    number: float_field(description="", default=5e-5, gt=0.0)
    boolean: bool_field(description="", default=True)
    obj: component_field(description="", parent="DummyConfigComponent")


class NormalParamComponent(DummyBaseConfigComponent):
    """A configurable component with normal params"""

    SCHEMA = NormalSchema

    def __init__(self, **kwargs) -> None:
        assert type(kwargs["integer"]) is int
        assert type(kwargs["string"]) is str
        assert type(kwargs["number"]) is float
        assert isinstance(kwargs["obj"], DummyBaseConfigComponent)


class NullSchema(BaseSchema):
    nullable_int: Optional[int_field(description="", default=1)]
    nullable_str: Optional[string_field(description="", default="", enum=[""])]
    nullable_obj: Optional[component_field(description="", parent="DummyBaseComponent")]


class NullParamComponent(DummyBaseConfigComponent):
    """A configurable component with nullable params"""

    SCHEMA = NullSchema

    def __init__(self, **kwargs):
        assert kwargs["nullable_int"] is None or type(kwargs["nullable_int"]) is int
        assert kwargs["nullable_str"] is None or type(kwargs["nullable_str"]) is str
        assert kwargs["nullable_obj"] is None or isinstance(
            kwargs["nullable_obj"], DummyBaseComponent
        )


class UnionSchema(BaseSchema):
    int_str: Union[
        int_field(description="", default=1),
        string_field(description="", default="foo", enum=["foo"]),
    ]
    int_obj: Union[
        int_field(description="", default=1),
        component_field(description="", parent="DummyBaseComponent"),
    ]


class UnionParamComponent(DummyBaseConfigComponent):
    """A configurable component with union params"""

    SCHEMA = UnionSchema

    def __init__(self, **kwargs):
        assert type(kwargs["int_str"]) is int or type(kwargs["int_str"]) is str
        assert type(kwargs["int_obj"]) is int or isinstance(
            kwargs["int_obj"], DummyBaseComponent
        )


@pytest.fixture(scope="module", autouse=True, name="test_registry")
def setup_test_registry(client):
    """Setup a test registry with test task, dataloader and model components."""
    container = client.app.container

    test_registry = ComponentRegistry(
        initial_components=[
            DummyBaseComponent,
            DummyComponent,
            DummyBaseConfigComponent,
            DummyParamComponent,
            NormalParamComponent,
            NullParamComponent,
            UnionParamComponent,
        ]
    )

    with container.component_registry.override(test_registry):
        yield test_registry


@pytest.fixture(scope="module", name="valid_union_params")
def fixture_valid_params() -> dict:
    return {
        "integer": 2,
        "string": "foo",
        "number": 5e-5,
        "boolean": True,
        "obj": {
            "component": "DummyParamComponent",
            "params": {
                "comp": {"component": "DummyComponent", "params": {"integer": 1}}
            },
        },
    }


def test_normal_schema(valid_union_params: dict):
    params = NormalParamComponent.SCHEMA.model_validate(valid_union_params)
    filled_params = fill_objects(params)
    NormalParamComponent(**filled_params)


def test_incorrect_type_in_normal_schema(valid_union_params: dict):
    invalid_params = valid_union_params.copy()
    invalid_params["integer"] = 1.1
    with pytest.raises(ValidationError, match="Input should be a valid integer"):
        NormalParamComponent.SCHEMA.model_validate(invalid_params)

    invalid_params = valid_union_params.copy()
    invalid_params["string"] = 2
    with pytest.raises(ValidationError, match="Input should be a valid string"):
        NormalParamComponent.SCHEMA.model_validate(invalid_params)

    invalid_params = valid_union_params.copy()
    invalid_params["number"] = ""
    with pytest.raises(ValidationError, match="Input should be a valid number"):
        NormalParamComponent.SCHEMA.model_validate(invalid_params)

    invalid_params = valid_union_params.copy()
    invalid_params["boolean"] = ""
    with pytest.raises(ValidationError, match="Input should be a valid boolean"):
        NormalParamComponent.SCHEMA.model_validate(invalid_params)

    invalid_params = valid_union_params.copy()
    invalid_params["obj"] = 1
    with pytest.raises(
        ValidationError,
        match="Input should be a valid dictionary or instance of ComponentType",
    ):
        NormalParamComponent.SCHEMA.model_validate(invalid_params)


def test_constraint_fails_in_normal_schema(valid_union_params: dict):
    invalid_params = valid_union_params.copy()
    invalid_params["integer"] = 1
    with pytest.raises(ValidationError, match="Input should be greater than or equal"):
        NormalParamComponent.SCHEMA.model_validate(invalid_params)

    invalid_params = valid_union_params.copy()
    invalid_params["integer"] = 3
    with pytest.raises(ValidationError, match="Input should be less than or equal"):
        NormalParamComponent.SCHEMA.model_validate(invalid_params)

    invalid_params = valid_union_params.copy()
    invalid_params["string"] = "foobar"
    with pytest.raises(ValidationError, match="foobar is not in the enum"):
        NormalParamComponent.SCHEMA.model_validate(invalid_params)


@pytest.fixture(scope="module", name="valid_null_params")
def fixture_valid_null_params() -> dict:
    return {"nullable_int": None, "nullable_str": None, "nullable_obj": None}


def test_null_schema(valid_null_params: dict):
    params = NullParamComponent.SCHEMA.model_validate(valid_null_params)
    filled_params = fill_objects(params)
    NullParamComponent(**filled_params)


def test_incorrect_type_in_null_schema(valid_null_params: dict):
    invalid_params = valid_null_params.copy()
    invalid_params["integer"] = None
    with pytest.raises(ValidationError, match="Input should be a valid integer"):
        NormalParamComponent.SCHEMA.model_validate(invalid_params)

    invalid_params = valid_null_params.copy()
    invalid_params["string"] = None
    with pytest.raises(ValidationError, match="Input should be a valid string"):
        NormalParamComponent.SCHEMA.model_validate(invalid_params)

    invalid_params = valid_null_params.copy()
    invalid_params["obj"] = None
    with pytest.raises(
        ValidationError,
        match="Input should be a valid dictionary or instance of ComponentType",
    ):
        NormalParamComponent.SCHEMA.model_validate(invalid_params)


@pytest.fixture(scope="module", name="valid_union_params_list")
def fixture_valid_union_params_list() -> List[dict]:
    return [
        {"int_str": 1, "int_obj": 1},
        {"int_str": "foo", "int_obj": 1},
        {"int_str": 1, "int_obj": {"component": "DummyComponent", "params": {}}},
        {"int_str": "foo", "int_obj": {"component": "DummyComponent", "params": {}}},
    ]


def test_union_schema(valid_union_params_list: List[dict]):
    for valid_union_params in valid_union_params_list:
        params = UnionParamComponent.SCHEMA.model_validate(valid_union_params)
        filled_params = fill_objects(params)
        UnionParamComponent(**filled_params)


def test_incorrect_type_in_union_schema(valid_union_params_list: List[dict]):
    for valid_union_params in valid_union_params_list:
        invalid_params = valid_union_params.copy()
        invalid_params["int_str"] = {
            "component": "DummyComponent",
            "params": {},
        }
        with pytest.raises(
            ValidationError,
            match=r"Input should be a valid integer|"
            r"Input should be a valid integer string",
        ):
            UnionParamComponent.SCHEMA.model_validate(invalid_params)

        invalid_params = valid_union_params.copy()
        invalid_params["int_obj"] = ""
        with pytest.raises(
            ValidationError,
            match=r"Input should be a valid integer|"
            r"Input should be a valid dictionary or instance of ComponentType",
        ):
            UnionParamComponent.SCHEMA.model_validate(invalid_params)
