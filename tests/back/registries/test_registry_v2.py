import pytest

from DashAI.back.config_object import ConfigObject
from DashAI.back.registries.registry import Registry

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


class BaseConfigComponent1(ConfigObject):
    TYPE = "ConfigComponent1"


class BaseConfigComponent2(ConfigObject):
    TYPE = "ConfigComponent2"


class BaseStaticComponent:
    TYPE = "StaticComponent"


class Component1(BaseConfigComponent1):
    @classmethod
    def get_schema(cls):
        return TEST_SCHEMA_1


class Component2(BaseConfigComponent1):
    @classmethod
    def get_schema(cls):
        return TEST_SCHEMA_2


class SubComponent1(Component1):
    @classmethod
    def get_schema(cls):
        return TEST_SCHEMA_1


class Component3(BaseStaticComponent):
    DESCRIPTION = "Some static component"


class ComponentWithTwoBaseClasses(BaseConfigComponent1, BaseConfigComponent2):
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


def test_basic_register_component():
    # this test does not include relationship creation.
    test_registy = Registry()
    test_registy.register_component(Component1)

    assert test_registy.registry == {
        "ConfigComponent1": {
            "Component1": {
                "name": "Component1",
                "type": "ConfigComponent1",
                "class": Component1,
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
            Component1,
            Component2,
            Component3,
        ]
    )
    assert hasattr(test_registry, "_registry")
    assert hasattr(test_registry, "registry")
    assert isinstance(test_registry.registry, dict)

    assert test_registry.registry == {
        "ConfigComponent1": {
            "Component1": {
                "name": "Component1",
                "type": "ConfigComponent1",
                "class": Component1,
                "configurable_object": True,
                "schema": {"properties": {"parameter_1": {"type": "number"}}},
                "description": None,
            },
            "Component2": {
                "name": "Component2",
                "type": "ConfigComponent1",
                "class": Component2,
                "configurable_object": True,
                "schema": {
                    "properties": {
                        "parameter_2": {"type": "string", "enum": ["a", "b"]}
                    }
                },
                "description": None,
            },
        },
        "StaticComponent": {
            "Component3": {
                "name": "Component3",
                "type": "StaticComponent",
                "class": Component3,
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
            r"Component ComponentWithTwoBaseClasses has more than one base "
            r"class with a 'TYPE' class attribute: "
            r"\['ComponentWithTwoBaseClasses', 'BaseConfigurableComponent1'"
            r", 'BaseConfigurableComponent2'\]."
        ),
    ):
        test_register._get_base_type(ComponentWithTwoBaseClasses)


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
    assert test_register._get_base_type(Component3) == "StaticComponent"
    assert test_register._get_base_type(Component1) == "ConfigComponent1"
    assert test_register._get_base_type(Component2) == "ConfigComponent1"


def test__contains__():
    test_registry = Registry(
        initial_components=[
            Component1,
            Component3,
        ]
    )

    assert "Component1" in test_registry
    assert "Component3" in test_registry
    assert "Component2" not in test_registry


def test__contains__key_type_error():
    test_registry = Registry(
        initial_components=[
            Component1,
            Component3,
        ]
    )
    with pytest.raises(TypeError, match=r"The key should be str, got \<.*\>."):
        Component1 in test_registry  # noqa


def test__getitem__():
    test_registry = Registry(
        initial_components=[
            Component1,
            Component2,
            Component3,
        ]
    )
    assert test_registry["Component1"] == {
        "name": "Component1",
        "type": "ConfigComponent1",
        "class": Component1,
        "configurable_object": True,
        "schema": TEST_SCHEMA_1,
        "description": None,
    }
    assert test_registry["Component2"] == {
        "name": "Component2",
        "type": "ConfigComponent1",
        "class": Component2,
        "configurable_object": True,
        "schema": TEST_SCHEMA_2,
        "description": None,
    }

    assert test_registry["Component3"] == {
        "name": "Component3",
        "type": "StaticComponent",
        "class": Component3,
        "configurable_object": False,
        "schema": None,
        "description": "Some static component",
    }


def test__getitem__key_type_error():
    test_registry = Registry(
        initial_components=[
            Component1,
            Component2,
        ]
    )

    with pytest.raises(
        TypeError,
        match=r"The indexer should be a string, got \<class .*\>.",
    ):
        test_registry[Component3]


def test__getitem__key_error():
    test_registry = Registry(
        initial_components=[
            Component1,
            Component2,
        ]
    )

    with pytest.raises(
        KeyError,
        match=r"Component 'StaticComponent1' does not exists in the registry.",
    ):
        test_registry["StaticComponent1"]


def test_get_components_by_type_select_and_ignore_none():
    test_registry = Registry(
        initial_components=[
            Component1,
            Component2,
            SubComponent1,
            Component3,
        ]
    )
    # test with one component type
    assert test_registry.get_components_by_type() == [
        "Component1",
        "Component2",
        "SubComponent1",
        "Component3",
    ]


def test_get_components_by_type_select_param():
    test_registry = Registry(
        initial_components=[
            Component1,
            Component2,
            SubComponent1,
            Component3,
        ]
    )
    # test with one component type
    assert test_registry.get_components_by_type(select="ConfigComponent1") == [
        "Component1",
        "Component2",
        "SubComponent1",
    ]

    # test with another component type
    assert test_registry.get_components_by_type(select="StaticComponent") == [
        "Component3"
    ]

    # test with one component type as list
    assert test_registry.get_components_by_type(select=["ConfigComponent1"]) == [
        "Component1",
        "Component2",
        "SubComponent1",
    ]

    # test with two component type as list
    assert test_registry.get_components_by_type(
        select=["ConfigComponent1", "StaticComponent"]
    ) == [
        "Component1",
        "Component2",
        "SubComponent1",
        "Component3",
    ]


def test_get_components_by_type_select_param_errors():
    test_registry = Registry(
        initial_components=[
            Component1,
            Component2,
            SubComponent1,
            Component3,
        ]
    )

    with pytest.raises(ValueError, match=r"Select list has not types to select."):
        test_registry.get_components_by_type(select=[])

    with pytest.raises(
        TypeError, match=r"Select must be a string or an array of strings, got 1."
    ):
        test_registry.get_components_by_type(select=1)

    with pytest.raises(
        TypeError, match=r"Select type at position 0 should be a string, got 1."
    ):
        test_registry.get_components_by_type(select=[1])

    with pytest.raises(
        TypeError, match=r"Select type at position 1 should be a string, got 1."
    ):
        test_registry.get_components_by_type(select=["ConfigComponent1", 1])

    with pytest.raises(
        ValueError,
        match=r"Component type UnexistantComponents does not exist in the registry.",
    ):
        test_registry.get_components_by_type(
            select=["ConfigComponent1", "UnexistantComponents"]
        )


def test_get_child_classes():
    test_registry = Registry(
        initial_components=[
            Component1,
            Component2,
            SubComponent1,
        ]
    )
    assert test_registry.get_child_classes("BaseConfigComponent1") == [
        "Component1",
        "Component2",
    ]
    assert test_registry.get_child_classes("BaseConfigComponent1", recursive=True) == [
        "Component1",
        "Component2",
        "SubComponent1",
    ]
    assert test_registry.get_child_classes("Component1") == ["SubComponent1"]
    assert test_registry.get_child_classes("BaseConfigComponent2") == []

    assert test_registry.get_child_classes("XYZ") == []
