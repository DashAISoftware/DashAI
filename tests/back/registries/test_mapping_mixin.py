import pytest

from DashAI.back.registries.base_registry import BaseRegistry
from DashAI.back.registries.register_mixins import TaskComponentMappingMixin
from DashAI.back.tasks import BaseTask


class TestComponentBase:
    __test__ = False


class TestTask1(BaseTask):
    __test__ = False


class TestTask2(BaseTask):
    __test__ = False


class TestTask3(BaseTask):
    __test__ = False


class NoCompatibleTasksComponent(TestComponentBase):
    pass


class WrongTypeCompatibleTasksComponent(TestComponentBase):
    _compatible_tasks = None


class EmptyCompatibleTasksComponent(TestComponentBase):
    _compatible_tasks = []


class NonExistantTaskComponent(TestComponentBase):
    _compatible_tasks = ["NotRegisteredTask"]


class TestComponent1(TestComponentBase):
    __test__ = False
    _compatible_tasks = ["TestTask1"]


class TestComponent2(TestComponentBase):
    __test__ = False
    _compatible_tasks = ["TestTask1"]


class TestComponent3(TestComponentBase):
    __test__ = False
    _compatible_tasks = ["TestTask2"]


class TestComponent4(TestComponentBase):
    __test__ = False
    _compatible_tasks = ["TestTask1", "TestTask2"]


class TestComponent5(TestComponentBase):
    __test__ = False
    _compatible_tasks = ["TestTask3"]


class TestTaskRegistry(BaseRegistry):
    __test__ = False
    registry_for = BaseTask


class TestComponentRegistry(BaseRegistry, TaskComponentMappingMixin):
    __test__ = False
    registry_for = TestComponentBase


@pytest.fixture()
def test_component_registry():
    task_registry = TestTaskRegistry(initial_components=[TestTask1, TestTask2])
    test_component_registry = TestComponentRegistry(
        initial_components=[],
        task_registry=task_registry,
    )
    return test_component_registry


def test_mapping_mixin_no_compatible_task(test_component_registry):
    with pytest.raises(
        AttributeError,
        match=(
            r"Component NoCompatibleTasksComponent has no _compatible_tasks attribute."
        ),
    ):
        test_component_registry.register_component(NoCompatibleTasksComponent)


def test_mapping_mixin_compatible_tasks_wrong_type(test_component_registry):
    with pytest.raises(
        TypeError,
        match=(
            r"Component WrongTypeCompatibleTasksComponent _compatible_tasks should "
            r"be a list, got None."
        ),
    ):
        test_component_registry.register_component(WrongTypeCompatibleTasksComponent)


def test_mapping_mixin_empty_compatible_tasks(test_component_registry):
    with pytest.raises(
        ValueError,
        match=(r"Component EmptyCompatibleTasksComponent has no associated tasks."),
    ):
        test_component_registry.register_component(EmptyCompatibleTasksComponent)


def test_mapping_mixin_non_existant_task(test_component_registry):
    with pytest.raises(
        KeyError,
        match=(
            r"Error when trying to associate component NonExistantTaskComponent "
            r"with its compatible tasks: task NotRegisteredTask does not exist in "
            r"the task registry."
        ),
    ):
        test_component_registry.register_component(NonExistantTaskComponent)


def test_mapping_mixin_mapping_when_register_component(test_component_registry):
    # add the first component  (compatible with task 1) and check mapping
    test_component_registry.register_component(TestComponent1)
    assert "TestTask1" in test_component_registry.task_component_mapping
    assert test_component_registry.task_component_mapping == {
        "TestTask1": ["TestComponent1"],
        "TestTask2": [],
    }

    # add the second component  (compatible with task 1) and check mapping
    test_component_registry.register_component(TestComponent2)

    assert "TestTask1" in test_component_registry.task_component_mapping
    assert test_component_registry.task_component_mapping == {
        "TestTask1": ["TestComponent1", "TestComponent2"],
        "TestTask2": [],
    }

    # add the third component (compatible with task 2) and check mapping
    test_component_registry.register_component(TestComponent3)
    assert "TestTask1" in test_component_registry.task_component_mapping
    assert test_component_registry.task_component_mapping == {
        "TestTask1": ["TestComponent1", "TestComponent2"],
        "TestTask2": ["TestComponent3"],
    }

    # add the fourth component (compatible with both tasks) and check mapping
    test_component_registry.register_component(TestComponent4)
    assert "TestTask1" in test_component_registry.task_component_mapping
    assert test_component_registry.task_component_mapping == {
        "TestTask1": ["TestComponent1", "TestComponent2", "TestComponent4"],
        "TestTask2": ["TestComponent3", "TestComponent4"],
    }

    ...


def test_mapping_mixin_mapping_with_runtime_new_task(test_component_registry):
    # add the first component  (compatible with task 1) and check mapping
    test_component_registry.register_component(TestComponent1)
    assert "TestTask1" in test_component_registry.task_component_mapping
    assert test_component_registry.task_component_mapping == {
        "TestTask1": ["TestComponent1"],
        "TestTask2": [],
    }
    test_component_registry._task_registry.register_component(TestTask3)
    test_component_registry.register_component(TestComponent5)
    assert test_component_registry.task_component_mapping == {
        "TestTask1": ["TestComponent1"],
        "TestTask2": [],
        "TestTask3": ["TestComponent5"],
    }


def test_task_to_components(test_component_registry):
    test_component_registry.register_component(TestComponent1)
    test_component_registry.register_component(TestComponent2)
    test_component_registry.register_component(TestComponent3)
    test_component_registry.register_component(TestComponent4)

    # check KeyError
    with pytest.raises(
        KeyError,
        match=r"Task1 does not exists in TestComponentRegistry task_component_mapping.",
    ):
        assert test_component_registry.task_to_components("Task1")

    assert test_component_registry.task_to_components("TestTask1") == [
        "TestComponent1",
        "TestComponent2",
        "TestComponent4",
    ]
    assert test_component_registry.task_to_components("TestTask2") == [
        "TestComponent3",
        "TestComponent4",
    ]


def test_component_to_task(test_component_registry):
    test_component_registry.register_component(TestComponent1)
    test_component_registry.register_component(TestComponent2)
    test_component_registry.register_component(TestComponent3)
    test_component_registry.register_component(TestComponent4)

    assert test_component_registry.component_to_tasks("TestComponent1") == ["TestTask1"]
    assert test_component_registry.component_to_tasks("TestComponent2") == ["TestTask1"]
    assert test_component_registry.component_to_tasks("TestComponent3") == ["TestTask2"]
    assert test_component_registry.component_to_tasks("TestComponent4") == [
        "TestTask1",
        "TestTask2",
    ]
