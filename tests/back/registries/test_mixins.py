from collections import defaultdict

import pytest

from DashAI.back.registries.base_registry import BaseRegistry
from DashAI.back.registries.mixins import RegisterInTaskCompatibleComponentsMixin
from DashAI.back.tasks import BaseTask


class OtherComponentBase:
    pass


class TestTask1(BaseTask):
    __test__ = False


class NoCompatibleTasksComponent(OtherComponentBase):
    pass


class WrongTypeCompatibleTasksComponent(OtherComponentBase):
    _compatible_tasks = None


class EmptyCompatibleTasksComponent(OtherComponentBase):
    _compatible_tasks = []


class NonExistantTaskComponent(OtherComponentBase):
    _compatible_tasks = ["TestTask2"]


class OkComponent(OtherComponentBase):
    _compatible_tasks = ["TestTask1"]
    pass


class TestTaskRegistry(BaseRegistry):
    __test__ = False
    registry_for = BaseTask


class OtherComponentRegistry(BaseRegistry, RegisterInTaskCompatibleComponentsMixin):
    __test__ = False
    registry_for = OtherComponentBase


@pytest.fixture()
def other_component_registry():
    task_registry = TestTaskRegistry(initial_components=[TestTask1])
    other_component_registry = OtherComponentRegistry(
        initial_components=[], task_registry=task_registry
    )
    return other_component_registry


def test_register_mixin_no_compatible_task(other_component_registry):
    with pytest.raises(
        AttributeError,
        match=(
            r"Component NoCompatibleTasksComponent has no _compatible_tasks attribute."
        ),
    ):
        other_component_registry.register_component(NoCompatibleTasksComponent)


def test_register_mixin_compatible_tasks_wrong_type(other_component_registry):
    with pytest.raises(
        TypeError,
        match=(
            r"Component WrongTypeCompatibleTasksComponent _compatible_tasks should "
            r"be a list, got None."
        ),
    ):
        other_component_registry.register_component(WrongTypeCompatibleTasksComponent)


def test_register_mixin_empty_compatible_tasks(other_component_registry):
    with pytest.raises(
        ValueError,
        match=(r"Component EmptyCompatibleTasksComponent has no associated tasks."),
    ):
        other_component_registry.register_component(EmptyCompatibleTasksComponent)


def test_register_mixin_non_existant_task(other_component_registry):
    with pytest.raises(
        ValueError,
        match=(
            r"Error while trying to register NonExistantTaskComponent into TestTask2:"
            " TestTask2 does not exists in the task registry."
        ),
    ):
        other_component_registry.register_component(NonExistantTaskComponent)


def test_register_mixin_successful_register(other_component_registry):
    other_component_registry.register_component(OkComponent)
    test_task = other_component_registry._task_registry["TestTask1"]
    assert isinstance(test_task.compatible_components, defaultdict)
    assert "OtherComponentBase" in test_task.compatible_components
    assert "OkComponent" in test_task.compatible_components["OtherComponentBase"]

    assert (
        test_task.compatible_components["OtherComponentBase"]["OkComponent"]
        == OkComponent
    )
