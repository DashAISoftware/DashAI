import pytest

from DashAI.back.config_object import ConfigObject
from DashAI.back.registries.base_registry_v2 import Registry

TEST_SCHEMA = {
    "properties": {
        "parameter_1": {
            "type": "number",
        },
        "parameter_2": {
            "type": "string",
            "enum": ["a", "b"],
        },
    }
}


class BaseTask:
    TYPE = "Task"


class BaseConfigurableComponent(ConfigObject):
    TYPE = "GenericComponent"


class BaseStaticComponent:
    TYPE = "StaticComponent"


class ConfigurableComponent1(BaseConfigurableComponent):
    @classmethod
    def get_schema(cls):
        return TEST_SCHEMA


class ConfigurableComponent2(BaseConfigurableComponent):
    @classmethod
    def get_schema(cls):
        return TEST_SCHEMA


class StaticComponent1(BaseStaticComponent):
    ...


class NoComponent:
    ...


def test__init__empty_tasks():
    # no initial components (by default None).
    test_registry = Registry()

    assert hasattr(test_registry, "_registry")
    assert hasattr(test_registry, "registry")
    assert hasattr(test_registry, "_relationship_manager")

    assert isinstance(test_registry._registry, dict)
    assert test_registry.registry == {}
    assert test_registry.registry == test_registry._registry

    # inital components as a empty list
    test_registry = Registry(initial_components=[])

    assert hasattr(test_registry, "_registry")
    assert hasattr(test_registry, "registry")
    assert hasattr(test_registry, "_relationship_manager")

    assert isinstance(test_registry._registry, dict)
    assert test_registry.registry == {}
    assert test_registry.registry == test_registry._registry


def test__init__bad_tasks_argument():
    with pytest.raises(
        TypeError,
        match=(r"new_component \"1\" should be a class, got <class 'int'>."),
    ):
        Registry(initial_components=[1, 2, 3])


def test__init__with_components():
    # init the test with two components
    test_registry = Registry(
        initial_components=[
            ConfigurableComponent1,
            ConfigurableComponent2,
            StaticComponent1,
        ]
    )
    assert hasattr(test_registry, "_registry")
    assert hasattr(test_registry, "registry")
    assert isinstance(test_registry.registry, dict)

    assert test_registry.registry == {
        "GenericComponent": {
            "ConfigurableComponent1": {
                "type": "GenericComponent",
                "class": ConfigurableComponent1,
                "configurable_object": True,
                "schema": TEST_SCHEMA,
            },
            "ConfigurableComponent2": {
                "type": "GenericComponent",
                "class": ConfigurableComponent2,
                "configurable_object": True,
                "schema": TEST_SCHEMA,
            },
            "StaticComponent1": {
                "type": "StaticComponent",
                "class": StaticComponent1,
                "configurable_object": False,
                "schema": None,
            },
        }
    }
