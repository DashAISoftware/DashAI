import pathlib
import shutil
import time
from abc import ABCMeta
from typing import Final, List

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from DashAI.back.app import create_app
from DashAI.back.config_object import ConfigObject
from DashAI.back.core.schema_fields import (
    BaseSchema,
    bool_field,
    component_field,
    enum_field,
    float_field,
    int_field,
    none_type,
    schema_field,
    union_type,
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
    comp: schema_field(
        component_field(parent="DummyBaseComponent"), placeholder={}, description=""
    )  # type: ignore
    integer: schema_field(int_field(), placeholder=1, description="")  # type: ignore


class DummyParamComponent(DummyBaseConfigComponent):
    """A configurable component that has another component as param."""

    SCHEMA = DummyParamComponentSchema

    def __init__(self, **kwargs):
        kwargs = self.validate_and_transform(kwargs)
        assert isinstance(kwargs["comp"], DummyBaseComponent)
        assert isinstance(kwargs["integer"], int)


class NormalSchema(BaseSchema):
    """Normal Schema for NormalParamComponent"""

    integer: schema_field(int_field(le=2, ge=2), placeholder=2, description="")  # type: ignore
    string: schema_field(
        enum_field(enum=["foo", "bar"]), placeholder="foo", description=""
    )  # type: ignore
    number: schema_field(float_field(gt=0.0), placeholder=5e-5, description="")  # type: ignore
    boolean: schema_field(bool_field(), placeholder=True, description="")  # type: ignore
    obj: schema_field(
        component_field(parent="DummyBaseConfigComponent"),
        placeholder={"component": "DummyParamComponent", "params": {}},
        description="",
    )  # type: ignore


class NormalParamComponent(DummyBaseConfigComponent):
    """A configurable component with normal params"""

    SCHEMA = NormalSchema

    def __init__(self, **kwargs) -> None:
        kwargs = self.validate_and_transform(kwargs)
        assert isinstance(kwargs["integer"], int)
        assert isinstance(kwargs["string"], str)
        assert isinstance(kwargs["number"], float)
        assert isinstance(kwargs["obj"], DummyBaseConfigComponent)


class NullSchema(BaseSchema):
    nullable_int: schema_field(none_type(int_field()), placeholder=1, description="")  # type: ignore
    nullable_str: schema_field(
        none_type(enum_field(enum=[""])), placeholder="", description=""
    )  # type: ignore
    nullable_obj: schema_field(
        none_type(component_field(parent="DummyBaseComponent")),
        placeholder={},
        description="",
    )  # type: ignore


class NullParamComponent(DummyBaseConfigComponent):
    """A configurable component with nullable params"""

    SCHEMA = NullSchema

    def __init__(self, **kwargs):
        kwargs = self.validate_and_transform(kwargs)
        assert kwargs["nullable_int"] is None or isinstance(kwargs["nullable_int"], int)
        assert kwargs["nullable_str"] is None or isinstance(kwargs["nullable_str"], str)
        assert kwargs["nullable_obj"] is None or isinstance(
            kwargs["nullable_obj"], DummyBaseComponent
        )


class UnionSchema(BaseSchema):
    """Union Schema for UnionParamComponent"""

    int_str: schema_field(
        union_type(int_field(), enum_field(enum=["foo"])),
        placeholder=1,
        description="",
    )  # type: ignore
    int_obj: schema_field(
        union_type(int_field(), component_field(parent="DummyBaseComponent")),
        placeholder=1,
        description="",
    )  # type: ignore


class UnionParamComponent(DummyBaseConfigComponent):
    """A configurable component with union params"""

    SCHEMA = UnionSchema

    def __init__(self, **kwargs):
        kwargs = self.validate_and_transform(kwargs)
        assert isinstance(kwargs["int_str"], (int, str))
        assert isinstance(kwargs["int_obj"], (int, DummyBaseComponent))


def remove_dir_with_retry(directory, max_attempts=5, sleep_seconds=1):
    for attempt in range(max_attempts):
        try:
            shutil.rmtree(directory)
            print(f"Successfully removed directory: {directory}")
            break
        except PermissionError as e:
            print(f"Attempt {attempt + 1} failed with error: {e}")
            time.sleep(sleep_seconds)
    else:
        print(f"Failed to remove directory after {max_attempts} attempts.")


@pytest.fixture(scope="module", autouse=True)
def client(test_path: pathlib.Path):
    app = create_app(
        local_path=test_path,
        logging_level="ERROR",
    )

    yield TestClient(app)

    app.container._services["engine"].dispose()
    remove_dir_with_retry(app.container._services["config"]["LOCAL_PATH"])


@pytest.fixture(autouse=True, name="test_registry")
def setup_test_registry(client, monkeypatch: pytest.MonkeyPatch):
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

    monkeypatch.setitem(
        container._services,
        "component_registry",
        test_registry,
    )
    return test_registry


def test_normal_json_schema():
    json_schema = NormalSchema.model_json_schema()
    assert set(json_schema.keys()) == {
        "description",
        "properties",
        "required",
        "title",
        "type",
    }
    assert isinstance(json_schema["description"], str)
    assert isinstance(json_schema["properties"], dict)
    assert set(json_schema["properties"].keys()) == {
        "integer",
        "string",
        "number",
        "boolean",
        "obj",
    }
    assert json_schema["properties"]["integer"]["type"] == "integer"
    assert json_schema["properties"]["integer"]["placeholder"] == 2
    assert json_schema["properties"]["integer"]["maximum"] == 2
    assert json_schema["properties"]["integer"]["minimum"] == 2
    assert json_schema["properties"]["string"]["type"] == "string"
    assert json_schema["properties"]["string"]["placeholder"] == "foo"
    assert json_schema["properties"]["string"]["enum"] == ["foo", "bar"]
    assert json_schema["properties"]["number"]["type"] == "number"
    assert json_schema["properties"]["number"]["placeholder"] == 5e-5
    assert json_schema["properties"]["number"]["exclusiveMinimum"] == 0.0
    assert json_schema["properties"]["boolean"]["type"] == "boolean"
    assert json_schema["properties"]["boolean"]["placeholder"] is True

    assert set(json_schema["properties"]["obj"].keys()) == {
        "description",
        "parent",
        "placeholder",
        "properties",
        "required",
        "title",
        "type",
    }
    assert isinstance(json_schema["properties"]["obj"]["properties"], dict)
    assert json_schema["properties"]["obj"]["parent"] == "DummyBaseConfigComponent"
    assert json_schema["properties"]["obj"]["placeholder"] == {
        "component": "DummyParamComponent",
        "params": {},
    }
    assert set(json_schema["properties"]["obj"]["properties"]) == {
        "component",
        "params",
    }
    assert (
        json_schema["properties"]["obj"]["properties"]["component"]["type"] == "string"
    )
    assert json_schema["properties"]["obj"]["properties"]["params"]["type"] == "object"
    assert set(json_schema["properties"]["obj"]["required"]) == {"component", "params"}
    assert json_schema["properties"]["obj"]["title"] == "Obj"
    assert json_schema["properties"]["obj"]["type"] == "object"

    assert set(json_schema["required"]) == {
        "integer",
        "string",
        "number",
        "boolean",
        "obj",
    }
    assert json_schema["title"] == "NormalSchema"
    assert json_schema["type"] == "object"


def test_union_json_schema():
    json_schema = UnionSchema.model_json_schema()
    assert set(json_schema.keys()) == {
        "description",
        "properties",
        "required",
        "title",
        "type",
    }
    assert isinstance(json_schema["description"], str)
    assert isinstance(json_schema["properties"], dict)
    assert set(json_schema["properties"].keys()) == {"int_str", "int_obj"}

    assert "anyOf" in json_schema["properties"]["int_str"]
    assert len(json_schema["properties"]["int_str"]["anyOf"]) == 2
    assert json_schema["properties"]["int_str"]["anyOf"][0]["type"] == "integer"
    assert json_schema["properties"]["int_str"]["anyOf"][1]["type"] == "string"
    assert json_schema["properties"]["int_str"]["placeholder"] == 1
    assert json_schema["properties"]["int_str"]["description"] == ""
    assert "anyOf" in json_schema["properties"]["int_obj"]
    assert len(json_schema["properties"]["int_obj"]["anyOf"]) == 2
    assert json_schema["properties"]["int_obj"]["anyOf"][0]["type"] == "integer"
    assert json_schema["properties"]["int_obj"]["anyOf"][1]["type"] == "object"
    assert json_schema["properties"]["int_obj"]["placeholder"] == 1
    assert json_schema["properties"]["int_obj"]["description"] == ""

    assert set(json_schema["required"]) == {"int_str", "int_obj"}
    assert json_schema["title"] == "UnionSchema"
    assert json_schema["type"] == "object"


@pytest.fixture(scope="module", name="valid_normal_params")
def fixture_valid_normal_params() -> dict:
    return {
        "integer": 2,
        "string": "foo",
        "number": 5e-5,
        "boolean": True,
        "obj": {
            "component": "DummyParamComponent",
            "params": {
                "comp": {"component": "DummyComponent", "params": {}},
                "integer": 1,
            },
        },
    }


def test_normal_schema(valid_normal_params: dict):
    NormalParamComponent(**valid_normal_params)


def test_incorrect_type_in_normal_schema(valid_normal_params: dict):
    invalid_params = valid_normal_params.copy()
    invalid_params["integer"] = 1.1
    with pytest.raises(ValidationError, match="Input should be a valid integer"):
        NormalParamComponent.SCHEMA.model_validate(invalid_params)

    invalid_params = valid_normal_params.copy()
    invalid_params["string"] = 2
    with pytest.raises(ValidationError, match="Input should be a valid string"):
        NormalParamComponent.SCHEMA.model_validate(invalid_params)

    invalid_params = valid_normal_params.copy()
    invalid_params["number"] = ""
    with pytest.raises(ValidationError, match="Input should be a valid number"):
        NormalParamComponent.SCHEMA.model_validate(invalid_params)

    invalid_params = valid_normal_params.copy()
    invalid_params["boolean"] = ""
    with pytest.raises(ValidationError, match="Input should be a valid boolean"):
        NormalParamComponent.SCHEMA.model_validate(invalid_params)

    invalid_params = valid_normal_params.copy()
    invalid_params["obj"] = 1
    with pytest.raises(
        ValidationError,
        match="Input should be a valid dictionary",
    ):
        NormalParamComponent.SCHEMA.model_validate(invalid_params)


def test_constraint_fails_in_normal_schema(valid_normal_params: dict):
    invalid_params = valid_normal_params.copy()
    invalid_params["integer"] = 1
    with pytest.raises(ValidationError, match="Input should be greater than or equal"):
        NormalParamComponent.SCHEMA.model_validate(invalid_params)

    invalid_params = valid_normal_params.copy()
    invalid_params["integer"] = 3
    with pytest.raises(ValidationError, match="Input should be less than or equal"):
        NormalParamComponent.SCHEMA.model_validate(invalid_params)

    invalid_params = valid_normal_params.copy()
    invalid_params["string"] = "foobar"
    with pytest.raises(ValidationError, match="foobar is not in the enum"):
        NormalParamComponent.SCHEMA.model_validate(invalid_params)


@pytest.fixture(scope="module", name="valid_null_params")
def fixture_valid_null_params() -> dict:
    return {"nullable_int": None, "nullable_str": None, "nullable_obj": None}


def test_null_schema(valid_null_params: dict):
    NullParamComponent(**valid_null_params)


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
        match="Input should be a valid dictionary",
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
        UnionParamComponent(**valid_union_params)


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
            r"Input should be a valid dictionary",
        ):
            UnionParamComponent.SCHEMA.model_validate(invalid_params)
