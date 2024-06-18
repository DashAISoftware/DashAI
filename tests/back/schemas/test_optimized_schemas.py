import copy

import pytest
from pydantic import ValidationError

from DashAI.back.config_object import ConfigObject
from DashAI.back.core.schema_fields import (
    optimizer_float_field,
    optimizer_int_field,
    schema_field,
)
from DashAI.back.core.schema_fields.base_schema import BaseSchema


class OptSchema(BaseSchema):
    opt_int: schema_field(
        optimizer_int_field(ge=0),
        {
            "optimize": False,
            "fixed_value": 0,
            "lower_bound": 1,
            "upper_bound": 3,
        },
        "",
    )  # type: ignore
    opt_float: schema_field(
        optimizer_float_field(gt=0.0),
        {
            "optimize": False,
            "fixed_value": 0.1,
            "lower_bound": 1.0,
            "upper_bound": 3.0,
        },
        "",
    )  # type: ignore


class DummyOptComponent(ConfigObject):
    SCHEMA = OptSchema

    def __init__(self, **kwargs) -> None:
        kwargs = self.validate_and_transform(kwargs)
        assert isinstance(kwargs["opt_int"]["fixed_value"], int)
        assert isinstance(kwargs["opt_int"]["lower_bound"], int)
        assert isinstance(kwargs["opt_float"]["upper_bound"], float)
        assert isinstance(kwargs["opt_float"]["optimize"], bool)


def test_opt_json_schema():
    json_schema = DummyOptComponent.get_schema()

    # Check field names
    assert set(json_schema["properties"].keys()) == {"opt_int", "opt_float"}
    # Check optimize int structure
    assert json_schema["properties"]["opt_int"]["type"] == "object"
    assert json_schema["properties"]["opt_int"]["placeholder"] == {
        "optimize": False,
        "fixed_value": 0,
        "lower_bound": 1,
        "upper_bound": 3,
    }
    assert (
        json_schema["properties"]["opt_int"]["properties"]["optimize"]["type"]
        == "boolean"
    )
    assert (
        json_schema["properties"]["opt_int"]["properties"]["fixed_value"]["type"]
        == "integer"
    )
    assert (
        json_schema["properties"]["opt_int"]["properties"]["lower_bound"]["type"]
        == "integer"
    )
    assert (
        json_schema["properties"]["opt_int"]["properties"]["upper_bound"]["type"]
        == "integer"
    )
    # Check optimize float structure
    assert json_schema["properties"]["opt_float"]["type"] == "object"
    assert json_schema["properties"]["opt_float"]["placeholder"] == {
        "optimize": False,
        "fixed_value": 0.1,
        "lower_bound": 1.0,
        "upper_bound": 3.0,
    }
    assert (
        json_schema["properties"]["opt_float"]["properties"]["optimize"]["type"]
        == "boolean"
    )
    assert (
        json_schema["properties"]["opt_float"]["properties"]["fixed_value"]["type"]
        == "number"
    )
    assert (
        json_schema["properties"]["opt_float"]["properties"]["lower_bound"]["type"]
        == "number"
    )
    assert (
        json_schema["properties"]["opt_float"]["properties"]["upper_bound"]["type"]
        == "number"
    )


@pytest.fixture(scope="module", name="valid_opt_params")
def fixture_valid_opt_params() -> dict:
    return {
        "opt_int": {
            "optimize": False,
            "fixed_value": 0,
            "lower_bound": 2,
            "upper_bound": 2,
        },
        "opt_float": {
            "optimize": True,
            "fixed_value": 0.1,
            "lower_bound": 1.5,
            "upper_bound": 2.0,
        },
    }


def test_opt_schema(valid_opt_params: dict):
    DummyOptComponent(**valid_opt_params)


def test_incorrect_type(valid_opt_params: dict):
    invalid_params = copy.deepcopy(valid_opt_params)
    invalid_params["opt_int"]["fixed_value"] = 1.1
    with pytest.raises(ValidationError, match="Input should be a valid integer"):
        DummyOptComponent.SCHEMA.model_validate(invalid_params)

    invalid_params = copy.deepcopy(valid_opt_params)
    invalid_params["opt_int"]["lower_bound"] = 1.1
    with pytest.raises(ValidationError, match="Input should be a valid integer"):
        DummyOptComponent.SCHEMA.model_validate(invalid_params)

    invalid_params = copy.deepcopy(valid_opt_params)
    invalid_params["opt_float"]["optimize"] = ""
    with pytest.raises(ValidationError, match="Input should be a valid boolean"):
        DummyOptComponent.SCHEMA.model_validate(invalid_params)

    invalid_params = copy.deepcopy(valid_opt_params)
    invalid_params["opt_float"]["upper_bound"] = ""
    with pytest.raises(ValidationError, match="Input should be a valid number"):
        DummyOptComponent.SCHEMA.model_validate(invalid_params)

    invalid_params = copy.deepcopy(valid_opt_params)
    invalid_params["opt_int"] = 1
    with pytest.raises(
        ValidationError,
        match="Input should be a valid dictionary",
    ):
        DummyOptComponent.SCHEMA.model_validate(invalid_params)


def test_constraint_fails(valid_opt_params: dict):
    invalid_params = copy.deepcopy(valid_opt_params)
    invalid_params["opt_int"]["lower_bound"] = 3
    with pytest.raises(
        ValidationError, match="lower_bound must be less or equal than upper_bound"
    ):
        DummyOptComponent.SCHEMA.model_validate(invalid_params)

    invalid_params = copy.deepcopy(valid_opt_params)
    invalid_params["opt_int"]["fixed_value"] = -1
    with pytest.raises(ValidationError, match="Input should be greater than or equal"):
        DummyOptComponent.SCHEMA.model_validate(invalid_params)

    invalid_params = copy.deepcopy(valid_opt_params)
    invalid_params["opt_float"]["fixed_value"] = -1
    with pytest.raises(ValidationError, match="Input should be greater than"):
        DummyOptComponent.SCHEMA.model_validate(invalid_params)
