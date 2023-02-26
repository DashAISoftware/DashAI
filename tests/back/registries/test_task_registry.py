import pytest

from DashAI.back.registries.task_registry import TaskRegistry
from DashAI.back.tasks.base_task import BaseTask


class TestTask1(BaseTask):
    name = "TestTask1"


class TestTask2(BaseTask):
    name = "TestTask2"


class TestTask3(BaseTask):
    name = "TestTask3"


class TestNoTask:
    name = "TestNoTask"


def test_task_registry__init__empty_tasks():
    task_registry = TaskRegistry(tasks=[])
    assert hasattr(task_registry, "_tasks")
    assert isinstance(task_registry._tasks, list)
    assert task_registry.tasks == []


def test_task_registry__init__bad_tasks_argument():
    with pytest.raises(TypeError, match=r""):
        TaskRegistry(tasks=None)


def test_task_registry__init__two_tasks():
    task_registry = TaskRegistry(tasks=[TestTask1, TestTask2])
    assert hasattr(task_registry, "_tasks")
    assert isinstance(task_registry._tasks, list)
    assert task_registry.tasks == [TestTask1, TestTask2]

    for task in task_registry._tasks:
        assert isinstance(task, BaseTask)


def test_task_registry_simple_register_task():
    task_registry = TaskRegistry(tasks=None)
    task_registry.register_task(TestTask1)
    assert hasattr(task_registry, "_tasks")

    assert task_registry.tasks == [TestTask1]

    task_registry.register_task(TestTask2)
    assert task_registry.tasks == [TestTask1, TestTask2]


def test_task_registry_register_task_with_defaults():
    task_registry = TaskRegistry(tasks=[TestTask1])
    assert hasattr(task_registry, "_tasks")
    assert task_registry.tasks == [TestTask1]

    task_registry.register_task(TestTask2)
    assert task_registry.tasks == [TestTask1, TestTask2]

    task_registry.register_task(TestTask3)
    assert task_registry.tasks == [TestTask1, TestTask2, TestTask3]


def test_task_registry_try_register_any_object():
    task_registry = TaskRegistry(tasks=[])

    with pytest.raises(ValueError, match="TODO"):
        task_registry.register_task(TestNoTask)
        task_registry.register_task(TestNoTask)
        task_registry.register_task(TestNoTask)
        task_registry.register_task(TestNoTask)
