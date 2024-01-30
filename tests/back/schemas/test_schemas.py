from abc import ABCMeta
from typing import List, Optional, Union

import pytest
from pydantic import ValidationError

from DashAI.back.config_object import ConfigObject
from DashAI.back.core.schema_fields import (
    BaseSchema,
    component_field,
    fill_objects,
    int_field,
    string_field,
)


class DummyConfigComponent(ConfigObject, metaclass=ABCMeta):
    pass


class DummyBaseComponent:
    pass


class DummyComponent(DummyBaseComponent):
    pass


class DummyParamComponentSchema(BaseSchema):
    comp: component_field(description="", parent="DummyBaseComponent")
    integer: int_field(description="", default=1)


class DummyParamComponent(DummyConfigComponent):
    SCHEMA = DummyParamComponentSchema

    def __init__(self, **kwargs):
        assert isinstance(kwargs["comp"], DummyBaseComponent)
        assert type(kwargs["integer"]) is int


class NormalSchema(BaseSchema):
    integer: int_field(description="", default=2, minimum=2, maximum=2)
    string: string_field(description="", default="foo", enum=["foo", "bar"])
    obj: component_field(
        description="", default="DummyParamComponent", parent="DummyConfigComponent"
    )


class NormalParamComponent(DummyConfigComponent):
    SCHEMA = NormalSchema

    def __init__(self, **kwargs) -> None:
        assert type(kwargs["integer"]) is int
        assert type(kwargs["string"]) is str
        assert isinstance(kwargs["obj"], DummyConfigComponent)


@pytest.fixture(scope="module", name="valid_union_params")
def fixture_valid_params() -> dict:
    return {
        "integer": 2,
        "string": "foo",
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
    NormalParamComponent(filled_params)


def test_incorrect_type(valid_union_params: dict):
    invalid_params = valid_union_params.copy()
    invalid_params["integer"] = "foo"
    with pytest.raises(ValidationError, match=""):
        NormalParamComponent.SCHEMA.model_validate(invalid_params)

    invalid_params = valid_union_params.copy()
    invalid_params["string"] = 2
    with pytest.raises(ValidationError, match=""):
        NormalParamComponent.SCHEMA.model_validate(invalid_params)

    invalid_params = valid_union_params.copy()
    invalid_params["obj"] = 1
    with pytest.raises(ValidationError, match=""):
        NormalParamComponent.SCHEMA.model_validate(invalid_params)


def test_constraint_fails(valid_union_params: dict):
    invalid_params = valid_union_params.copy()
    invalid_params["integer"] = 1
    with pytest.raises(ValidationError, match=""):
        NormalParamComponent.SCHEMA.model_validate(invalid_params)

    invalid_params = valid_union_params.copy()
    invalid_params["integer"] = 3
    with pytest.raises(ValidationError, match=""):
        NormalParamComponent.SCHEMA.model_validate(invalid_params)

    invalid_params = valid_union_params.copy()
    invalid_params["string"] = "foobar"
    with pytest.raises(ValidationError, match=""):
        NormalParamComponent.SCHEMA.model_validate(invalid_params)

    invalid_params = valid_union_params.copy()
    invalid_params["obj"] = {"component": "AnotherComponent", "params": {}}
    with pytest.raises(ValidationError, match=""):
        NormalParamComponent.SCHEMA.model_validate(invalid_params)


class NullSchema(BaseSchema):
    nullable_int: Optional[int_field(description="", default=1)]
    nullable_str: Optional[string_field(description="", default="", enum=[""])]
    nullable_obj: Optional[
        component_field(
            description="", default="DummyComponent", parent="DummyBaseComponent"
        )
    ]


class NullParamComponent(DummyConfigComponent):
    SCHEMA = NullSchema

    def __init__(self, **kwargs):
        assert kwargs["nullable_int"] is None or type(kwargs["nullable_int"]) is int
        assert kwargs["nullable_str"] is None or type(kwargs["nullable_str"]) is str
        assert kwargs["nullable_obj"] is None or isinstance(
            kwargs["nullable_obj"], DummyBaseComponent
        )


@pytest.fixture(scope="module", name="valid_null_params")
def fixture_valid_null_params() -> dict:
    return {"nullable_int": None, "nullable_str": None, "nullable_obj": None}


def test_normal_null_schema(valid_null_params: dict):
    params = NullParamComponent.SCHEMA.model_validate(valid_null_params)
    filled_params = fill_objects(params)
    NullParamComponent(filled_params)


def test_incorrect_null_type(valid_null_params: dict):
    invalid_params = valid_null_params.copy()
    invalid_params["nullable_int"] = None
    with pytest.raises(ValidationError, match=""):
        NullParamComponent.SCHEMA.model_validate(invalid_params)

    invalid_params = valid_null_params.copy()
    invalid_params["nullable_str"] = None
    with pytest.raises(ValidationError, match=""):
        NullParamComponent.SCHEMA.model_validate(invalid_params)

    invalid_params = valid_null_params.copy()
    invalid_params["nullable_obj"] = None
    with pytest.raises(ValidationError, match=""):
        NullParamComponent.SCHEMA.model_validate(invalid_params)


class UnionSchema(BaseSchema):
    int_str: Union[
        int_field(description="", default=1),
        string_field(description="", default="foo", enum=["foo"]),
    ]
    int_obj: Union[
        int_field(description="", default=1),
        component_field(
            description="", default="DummyComponent", parent="DummyBaseComponent"
        ),
    ]


class UnionParamComponent(DummyConfigComponent):
    SCHEMA = UnionSchema

    def __init__(self, **kwargs):
        assert type(kwargs["int_str"]) is int or type(kwargs["int_str"]) is int
        assert type(kwargs["int_obj"]) is int or isinstance(
            kwargs["int_obj"], DummyBaseComponent
        )


@pytest.fixture(scope="module", name="valid_union_params_list")
def fixture_valid_union_params_list() -> List[dict]:
    return [
        {"int_str": 1, "int_obj": 1},
        {"int_str": "", "int_obj": 1},
        {"int_str": 1, "int_obj": {"component": "DummyComponent", "params": {}}},
        {"int_str": "", "int_obj": {"component": "DummyComponent", "params": {}}},
    ]


def test_normal_union_schema(valid_union_params_list: List[dict]):
    for valid_union_params in valid_union_params_list:
        params = UnionParamComponent.SCHEMA.model_validate(valid_union_params)
        filled_params = fill_objects(params)
        UnionParamComponent(filled_params)


def test_incorrect_union_type(valid_union_params_list: List[dict]):
    for valid_union_params in valid_union_params_list:
        invalid_params = valid_union_params.copy()
        invalid_params["int_str"] = {
            "component": "DummyComponent",
            "params": {},
        }
        with pytest.raises(ValidationError, match=""):
            NullParamComponent.SCHEMA.model_validate(invalid_params)

        invalid_params = valid_union_params.copy()
        invalid_params["int_obj"] = ""
        with pytest.raises(ValidationError, match=""):
            NullParamComponent.SCHEMA.model_validate(invalid_params)
