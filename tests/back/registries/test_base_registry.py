import pytest

from DashAI.back.registries.base_registry import BaseRegistry


class BaseComponent:
    pass


class Component1(BaseComponent):
    pass


class Component2(BaseComponent):
    pass


class Component3(BaseComponent):
    pass


class NoComponent:
    pass


class TestRegistry(BaseRegistry):
    __test__ = False
    registry_for = BaseComponent


def test__init__empty_tasks():
    test_registry = TestRegistry(initial_components=[])

    assert hasattr(test_registry, "_registry")
    assert hasattr(test_registry, "registry")
    assert isinstance(test_registry._registry, dict)
    assert test_registry.registry == {}
    assert test_registry.registry == test_registry._registry


def test__init__bad_tasks_argument():
    with pytest.raises(
        TypeError,
        match=(
            r"initial_components should be a list of BaseComponent subclasses, "
            r"got None."
        ),
    ):
        TestRegistry(initial_components=None)


def test__init__empty_initial_components():
    test_registry = TestRegistry(initial_components=[])

    # register Component1
    test_registry.register_component(Component1)
    assert test_registry.registry == {"Component1": Component1}

    # register Component2
    test_registry.register_component(Component2)
    assert test_registry.registry == {
        "Component1": Component1,
        "Component2": Component2,
    }


def test__init__with_two_components():
    # init the test with two components
    test_registry = TestRegistry(initial_components=[Component1, Component2])
    assert hasattr(test_registry, "_registry")
    assert hasattr(test_registry, "registry")
    assert isinstance(test_registry.registry, dict)
    assert test_registry.registry == {
        "Component1": Component1,
        "Component2": Component2,
    }

    for components in test_registry.registry:
        assert issubclass(test_registry.registry[components], BaseComponent)


def test__contains():
    test_registry = TestRegistry(initial_components=[Component1, Component2])

    assert "Component1" in test_registry
    assert "Component2" in test_registry
    assert "Component3" not in test_registry
    assert None not in test_registry


def test__getitem__():
    test_registry = TestRegistry(initial_components=[Component1, Component2])
    with pytest.raises(
        TypeError,
        match="The indexer should be a string, got None.",
    ):
        test_registry[None]

    with pytest.raises(
        KeyError,
        match="'TaskX does not exists in the BaseComponent registry.",
    ):
        test_registry["TaskX"]

    assert test_registry["Component1"] == Component1
    assert test_registry["Component2"] == Component2


def test_register_wrong_type():
    test_registry = TestRegistry(initial_components=[])
    with pytest.raises(
        TypeError,
        match=(r"new_component should be a class, got None."),
    ):
        test_registry.register_component(None)


def test_register_no_subclass():
    test_registry = TestRegistry(initial_components=[])

    with pytest.raises(
        TypeError,
        match=(
            r"new_component should be a subclass of BaseComponent, "
            r"got <class 'tests.back.registries.test_base_registry.NoComponent'>."
        ),
    ):
        test_registry.register_component(NoComponent)


def test__init__wrong_type():
    with pytest.raises(
        TypeError,
        match=(r"new_component should be a class, got None."),
    ):
        TestRegistry(initial_components=[Component1, None])


def test__init__try_register_no_subclass():
    with pytest.raises(
        TypeError,
        match=(
            r"new_component should be a subclass of BaseComponent, "
            r"got <class 'tests.back.registries.test_base_registry.NoComponent'>."
        ),
    ):
        TestRegistry(initial_components=[Component1, NoComponent])
