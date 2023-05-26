import pytest

from DashAI.back.config_object import ConfigObject
from DashAI.back.registries.base_registry_v2 import Registry

TEST_SCHEMA_1 = {
    "properties": {
        "parameter_1": {
            "type": "number",
        },
    }
}

TEST_SCHEMA_2 = {
    "properties": {
        "parameter_2": {
            "type": "string",
            "enum": ["a", "b"],
        },
    }
}


class BaseTask:
    TYPE = "Task"


class BaseConfigurableComponent1(ConfigObject):
    TYPE = "GenericComponent1"


class BaseConfigurableComponent2(ConfigObject):
    TYPE = "GenericComponent2"


class BaseStaticComponent:
    TYPE = "StaticComponent"


class ConfigurableComponent1(BaseConfigurableComponent1):
    @classmethod
    def get_schema(cls):
        return TEST_SCHEMA_1


class ConfigurableComponent2(BaseConfigurableComponent1):
    @classmethod
    def get_schema(cls):
        return TEST_SCHEMA_2


class SubConfigurableComponent1(ConfigurableComponent1):
    @classmethod
    def get_schema(cls):
        return TEST_SCHEMA_1


class ConfigurableComponentWithTwoBaseClasses(
    BaseConfigurableComponent1, BaseConfigurableComponent2
):
    ...


class StaticComponent1(BaseStaticComponent):
    DESCRIPTION = "Some static component"


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


def test_basic_register_component():
    # this test does not include relationship creation.
    test_registy = Registry()
    test_registy.register_component(ConfigurableComponent1)

    assert test_registy.registry == {
        "GenericComponent1": {
            "ConfigurableComponent1": {
                "type": "GenericComponent1",
                "class": ConfigurableComponent1,
                "configurable_object": True,
                "schema": TEST_SCHEMA_1,
                "description": None,
            }
        }
    }


def test_basic_register_component_class_with_no_type():
    # this test does not include relationship creation.
    test_registy = Registry()

    with pytest.raises(
        TypeError,
        match=(
            r"Component NoComponent does not a DashAI base class with a 'TYPE' "
            r"class attribute.*"
        ),
    ):
        test_registy.register_component(NoComponent)


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
        "GenericComponent1": {
            "ConfigurableComponent1": {
                "type": "GenericComponent1",
                "class": ConfigurableComponent1,
                "configurable_object": True,
                "schema": TEST_SCHEMA_1,
                "description": None,
            },
            "ConfigurableComponent2": {
                "type": "GenericComponent1",
                "class": ConfigurableComponent2,
                "configurable_object": True,
                "schema": TEST_SCHEMA_2,
                "description": None,
            },
        },
        "StaticComponent": {
            "StaticComponent1": {
                "type": "StaticComponent",
                "class": StaticComponent1,
                "configurable_object": False,
                "schema": None,
                "description": "Some static component",
            }
        },
    }


def test_get_base_type_two_base_classes_typerror():
    test_register = Registry()
    with pytest.raises(
        TypeError,
        match=(
            r"Component ConfigurableComponentWithTwoBaseClasses has more than one base "
            r"class with a 'TYPE' class attribute: "
            r"\['ConfigurableComponentWithTwoBaseClasses', 'BaseConfigurableComponent1'"
            r", 'BaseConfigurableComponent2'\]."
        ),
    ):
        test_register._get_base_type(ConfigurableComponentWithTwoBaseClasses)


def test_get_base_type_no_base_classes_typerror():
    test_register = Registry()
    with pytest.raises(
        TypeError,
        match=(
            r"Component NoComponent does not a DashAI base class with a 'TYPE' class "
            r"attribute.*"
        ),
    ):
        test_register._get_base_type(NoComponent)


def test_get_base_type():
    test_register = Registry()
    assert test_register._get_base_type(StaticComponent1) == "StaticComponent"
    assert test_register._get_base_type(ConfigurableComponent1) == "GenericComponent1"
    assert test_register._get_base_type(ConfigurableComponent2) == "GenericComponent1"


def test__contains__():
    test_registry = Registry(
        initial_components=[
            ConfigurableComponent1,
            StaticComponent1,
        ]
    )

    assert "ConfigurableComponent1" in test_registry
    assert "StaticComponent1" in test_registry
    assert "ConfigurableComponent2" not in test_registry


def test__contains__key_type_error():
    test_registry = Registry(
        initial_components=[
            ConfigurableComponent1,
            StaticComponent1,
        ]
    )
    with pytest.raises(TypeError, match=r"The key should be str, got \<.*\>."):
        ConfigurableComponent1 in test_registry  # noqa


def test__getitem__():
    test_registry = Registry(
        initial_components=[
            ConfigurableComponent1,
            ConfigurableComponent2,
            StaticComponent1,
        ]
    )
    assert test_registry["ConfigurableComponent1"] == {
        "type": "GenericComponent1",
        "class": ConfigurableComponent1,
        "configurable_object": True,
        "schema": TEST_SCHEMA_1,
        "description": None,
    }
    assert test_registry["ConfigurableComponent2"] == {
        "type": "GenericComponent1",
        "class": ConfigurableComponent2,
        "configurable_object": True,
        "schema": TEST_SCHEMA_2,
        "description": None,
    }

    assert test_registry["StaticComponent1"] == {
        "type": "StaticComponent",
        "class": StaticComponent1,
        "configurable_object": False,
        "schema": None,
        "description": "Some static component",
    }


def test__getitem__key_type_error():
    test_registry = Registry(
        initial_components=[
            ConfigurableComponent1,
            ConfigurableComponent2,
        ]
    )

    with pytest.raises(
        TypeError,
        match=r"The indexer should be a string, got \<class .*\>.",
    ):
        test_registry[StaticComponent1]


def test__getitem__key_error():
    test_registry = Registry(
        initial_components=[
            ConfigurableComponent1,
            ConfigurableComponent2,
        ]
    )

    with pytest.raises(
        KeyError,
        match=r"Component 'StaticComponent1' does not exists in the registry.",
    ):
        test_registry["StaticComponent1"]


def test_get_child_classes():
    test_registry = Registry(
        initial_components=[
            ConfigurableComponent1,
            ConfigurableComponent2,
            SubConfigurableComponent1,
        ]
    )
    assert test_registry.get_child_classes("BaseConfigurableComponent1") == [
        "ConfigurableComponent1",
        "ConfigurableComponent2",
    ]
    assert test_registry.get_child_classes("ConfigurableComponent1") == [
        "SubConfigurableComponent1"
    ]
    assert test_registry.get_child_classes("ConfigurableComponent2") == []

    assert test_registry.get_child_classes("XYZ") == []
