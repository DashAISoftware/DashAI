import pytest

from DashAI.back.src.base import BaseTask
from DashAI.back.src.registry import TaskRegistry


class TestTask1(BaseTask):
    pass


class TestTask2(BaseTask):
    pass


class TestTask3(BaseTask):
    pass


class TestNoTask:
    pass


def test_task_registry__init__():

    task_registry = TaskRegistry()
    assert hasattr(task_registry, "_tasks")
    assert task_registry.tasks == []

    task_registry = TaskRegistry(default_tasks=None)
    assert hasattr(task_registry, "_tasks")
    assert task_registry.tasks == []

    task_registry = TaskRegistry(default_tasks=[TestTask1, TestTask2])
    assert hasattr(task_registry, "_tasks")
    assert task_registry.tasks == [TestTask1, TestTask2]


def test_task_registry_simple_register_task():
    task_registry = TaskRegistry(default_tasks=None)
    task_registry.register_task(TestTask1)
    assert hasattr(task_registry, "_tasks")

    assert task_registry.tasks == [TestTask1]

    task_registry.register_task(TestTask2)
    assert task_registry.tasks == [TestTask1, TestTask2]


def test_task_registry_register_task_with_defaults():
    task_registry = TaskRegistry(default_tasks=[TestTask1])
    assert hasattr(task_registry, "_tasks")
    assert task_registry.tasks == [TestTask1]

    task_registry.register_task(TestTask2)
    assert task_registry.tasks == [TestTask1, TestTask2]

    task_registry.register_task(TestTask3)
    assert task_registry.tasks == [TestTask1, TestTask2, TestTask3]


def test_task_registry_try_register_any_object():
    task_registry = TaskRegistry(default_tasks=[])

    with pytest.raises(ValueError, match="TODO"):
        task_registry.register_task(TestNoTask)
