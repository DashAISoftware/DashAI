import pytest

from DashAI.back.config_object import ConfigObject
from DashAI.back.registries.component_registry import ComponentRegistry

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


class RelatedComponent1(BaseStaticComponent):
    COMPATIBLE_COMPONENTS = ["Component1"]


class RelatedComponent2(BaseStaticComponent):
    COMPATIBLE_COMPONENTS = ["Component1", "Component2"]


class ComponentWithTwoBaseClasses(BaseConfigComponent1, BaseConfigComponent2):
    ...


class NoComponent:
    ...


COMPONENT1_DICT = {
    "name": "Component1",
    "type": "ConfigComponent1",
    "class": Component1,
    "configurable_object": True,
    "schema": {"properties": {"parameter_1": {"type": "number"}}},
    "description": None,
}
COMPONENT2_DICT = {
    "name": "Component2",
    "type": "ConfigComponent1",
    "class": Component2,
    "configurable_object": True,
    "schema": {"properties": {"parameter_2": {"type": "string", "enum": ["a", "b"]}}},
    "description": None,
}
SUBCOMPONENT1_DICT = {
    "name": "SubComponent1",
    "type": "ConfigComponent1",
    "class": SubComponent1,
    "configurable_object": True,
    "schema": {"properties": {"parameter_1": {"type": "number"}}},
    "description": None,
}
COMPONENT3_DICT = {
    "name": "Component3",
    "type": "StaticComponent",
    "class": Component3,
    "configurable_object": False,
    "schema": None,
    "description": "Some static component",
}
RELATED_COMPONENT1_DICT = {
    "name": "RelatedComponent1",
    "type": "StaticComponent",
    "class": RelatedComponent1,
    "configurable_object": False,
    "schema": None,
    "description": None,
}
RELATED_COMPONENT2_DICT = {
    "name": "RelatedComponent2",
    "type": "StaticComponent",
    "class": RelatedComponent2,
    "configurable_object": False,
    "schema": None,
    "description": None,
}


def test__init__empty_tasks():
    # no initial components (by default None).
    test_registry = ComponentRegistry()

    assert hasattr(test_registry, "_registry")
    assert hasattr(test_registry, "registry")
    assert hasattr(test_registry, "_relationship_manager")

    assert isinstance(test_registry._registry, dict)
    assert test_registry.registry == {}
    assert test_registry.registry == test_registry._registry

    # inital components as a empty list
    test_registry = ComponentRegistry(initial_components=[])

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
        ComponentRegistry(initial_components=[1, 2, 3])


def test_basic_register_component():
    # this test does not include relationship creation.
    test_registy = ComponentRegistry()
    test_registy.register_component(Component1)

    assert test_registy.registry == {
        "ConfigComponent1": {"Component1": COMPONENT1_DICT}
    }


def test_basic_register_component_class_with_no_type():
    # this test does not include relationship creation.
    test_registy = ComponentRegistry()

    with pytest.raises(
        TypeError,
        match=(
            r"Component NoComponent does not inherit from any DashAI base class with "
            r"a 'TYPE' class attribute.*"
        ),
    ):
        test_registy.register_component(NoComponent)


def test__init__with_components():
    # init the test with two components
    test_registry = ComponentRegistry(
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
            "Component1": COMPONENT1_DICT,
            "Component2": COMPONENT2_DICT,
        },
        "StaticComponent": {"Component3": COMPONENT3_DICT},
    }


def test_get_base_type_two_base_classes_typerror():
    test_register = ComponentRegistry()
    with pytest.raises(
        TypeError,
        match=(
            r"Component ComponentWithTwoBaseClasses has more than one base "
            r"class with a 'TYPE' class attribute: "
            r"\['ComponentWithTwoBaseClasses', 'BaseConfigComponent1'"
            r", 'BaseConfigComponent2'\]."
        ),
    ):
        test_register._get_base_type(ComponentWithTwoBaseClasses)


def test_get_base_type_no_base_classes_typerror():
    test_register = ComponentRegistry()
    with pytest.raises(
        TypeError,
        match=(
            r"Component NoComponent does not inherit from any DashAI base class "
            r"with a 'TYPE' class attribute.*"
        ),
    ):
        test_register._get_base_type(NoComponent)


def test_get_base_type():
    test_register = ComponentRegistry()
    assert test_register._get_base_type(Component3) == "StaticComponent"
    assert test_register._get_base_type(Component1) == "ConfigComponent1"
    assert test_register._get_base_type(Component2) == "ConfigComponent1"


def test__contains__():
    test_registry = ComponentRegistry(
        initial_components=[
            Component1,
            Component3,
        ]
    )

    assert "Component1" in test_registry
    assert "Component3" in test_registry
    assert "Component2" not in test_registry


def test__contains__key_type_error():
    test_registry = ComponentRegistry(
        initial_components=[
            Component1,
            Component3,
        ]
    )
    with pytest.raises(TypeError, match=r"The key should be str, got \<.*\>."):
        Component1 in test_registry  # noqa


def test__getitem__():
    test_registry = ComponentRegistry(
        initial_components=[
            Component1,
            Component2,
            Component3,
        ]
    )
    assert test_registry["Component1"] == COMPONENT1_DICT
    assert test_registry["Component2"] == COMPONENT2_DICT
    assert test_registry["Component3"] == COMPONENT3_DICT


def test__getitem__key_type_error():
    test_registry = ComponentRegistry(
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
    test_registry = ComponentRegistry(
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
    test_registry = ComponentRegistry(
        initial_components=[
            Component1,
            Component2,
            SubComponent1,
            Component3,
        ]
    )
    # test with one component type
    assert test_registry.get_components_by_types() == [
        COMPONENT1_DICT,
        COMPONENT2_DICT,
        SUBCOMPONENT1_DICT,
        COMPONENT3_DICT,
    ]


def test_get_components_by_type_select_param():
    test_registry = ComponentRegistry(
        initial_components=[
            Component1,
            Component2,
            SubComponent1,
            Component3,
        ]
    )
    # test with one component type
    assert test_registry.get_components_by_types(select="ConfigComponent1") == [
        COMPONENT1_DICT,
        COMPONENT2_DICT,
        SUBCOMPONENT1_DICT,
    ]

    # test with another component type
    assert test_registry.get_components_by_types(select="StaticComponent") == [
        COMPONENT3_DICT
    ]

    # test with one component type as list
    assert test_registry.get_components_by_types(select=["ConfigComponent1"]) == [
        COMPONENT1_DICT,
        COMPONENT2_DICT,
        SUBCOMPONENT1_DICT,
    ]

    # test with two component type as list
    assert test_registry.get_components_by_types(
        select=["ConfigComponent1", "StaticComponent"]
    ) == [COMPONENT1_DICT, COMPONENT2_DICT, SUBCOMPONENT1_DICT, COMPONENT3_DICT]


def test_get_components_by_type_select_param_errors():
    test_registry = ComponentRegistry(
        initial_components=[
            Component1,
            Component2,
            SubComponent1,
            Component3,
        ]
    )

    with pytest.raises(ValueError, match=r"Select list has not types to select."):
        test_registry.get_components_by_types(select=[])

    with pytest.raises(
        TypeError, match=r"Select must be a string or an array of strings, got 1."
    ):
        test_registry.get_components_by_types(select=1)

    with pytest.raises(
        TypeError, match=r"Select type at position 0 should be a string, got 1."
    ):
        test_registry.get_components_by_types(select=[1])

    with pytest.raises(
        TypeError, match=r"Select type at position 1 should be a string, got 1."
    ):
        test_registry.get_components_by_types(select=["ConfigComponent1", 1])

    with pytest.raises(
        ValueError,
        match=r"Component type UnexistantComponents does not exist in the registry.",
    ):
        test_registry.get_components_by_types(
            select=["ConfigComponent1", "UnexistantComponents"]
        )


def test_get_components_by_type_ignore_param():
    test_registry = ComponentRegistry(
        initial_components=[
            Component1,
            Component2,
            SubComponent1,
            Component3,
        ]
    )
    # test with another component type
    assert test_registry.get_components_by_types(ignore="ConfigComponent1") == [
        COMPONENT3_DICT
    ]
    # test with one component type
    assert test_registry.get_components_by_types(ignore="StaticComponent") == [
        COMPONENT1_DICT,
        COMPONENT2_DICT,
        SUBCOMPONENT1_DICT,
    ]

    # test with one component type as list
    assert test_registry.get_components_by_types(ignore=["ConfigComponent1"]) == [
        COMPONENT3_DICT
    ]

    # test with two component type as list
    assert (
        test_registry.get_components_by_types(
            ignore=["ConfigComponent1", "StaticComponent"]
        )
        == []
    )


def test_get_components_by_type_ignore_param_errors():
    test_registry = ComponentRegistry(
        initial_components=[
            Component1,
            Component2,
            SubComponent1,
            Component3,
        ]
    )

    with pytest.raises(ValueError, match=r"Ignore list has not types to select."):
        test_registry.get_components_by_types(ignore=[])

    with pytest.raises(
        TypeError, match=r"Ignore must be a string or an array of strings, got 1."
    ):
        test_registry.get_components_by_types(ignore=1)

    with pytest.raises(
        TypeError, match=r"Ignore type at position 0 should be a string, got 1."
    ):
        test_registry.get_components_by_types(ignore=[1])

    with pytest.raises(
        TypeError, match=r"Ignore type at position 1 should be a string, got 1."
    ):
        test_registry.get_components_by_types(ignore=["ConfigComponent1", 1])

    with pytest.raises(
        ValueError,
        match=r"Component type UnexistantComponents does not exist in the registry.",
    ):
        test_registry.get_components_by_types(
            ignore=["ConfigComponent1", "UnexistantComponents"]
        )


def test_get_child_classes():
    test_registry = ComponentRegistry(
        initial_components=[
            Component1,
            Component2,
            SubComponent1,
        ]
    )
    assert test_registry.get_child_components("BaseConfigComponent1") == [
        COMPONENT1_DICT,
        COMPONENT2_DICT,
    ]
    assert test_registry.get_child_components(
        "BaseConfigComponent1", recursive=True
    ) == [
        COMPONENT1_DICT,
        COMPONENT2_DICT,
        SUBCOMPONENT1_DICT,
    ]
    assert test_registry.get_child_components("Component1") == [SUBCOMPONENT1_DICT]
    assert test_registry.get_child_components("BaseConfigComponent2") == []

    assert test_registry.get_child_components("XYZ") == []


def test_relationships_module():
    test_registry = ComponentRegistry(
        initial_components=[
            Component1,
            Component2,
            SubComponent1,
        ]
    )

    test_registry.register_component(RelatedComponent1)
    test_registry.register_component(RelatedComponent2)

    assert test_registry._relationship_manager.relations == {
        "RelatedComponent1": ["Component1"],
        "Component1": ["RelatedComponent1", "RelatedComponent2"],
        "RelatedComponent2": ["Component1", "Component2"],
        "Component2": ["RelatedComponent2"],
    }

    assert test_registry.get_related_components("Component1") == [
        RELATED_COMPONENT1_DICT,
        RELATED_COMPONENT2_DICT,
    ]

    assert test_registry.get_related_components("Component2") == [
        RELATED_COMPONENT2_DICT
    ]

    assert test_registry.get_related_components("SubComponent1") == []

    assert test_registry.get_related_components("RelatedComponent1") == [
        COMPONENT1_DICT
    ]

    assert test_registry.get_related_components("RelatedComponent2") == [
        COMPONENT1_DICT,
        COMPONENT2_DICT,
    ]
