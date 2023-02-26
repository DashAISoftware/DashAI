import pytest

from DashAI.back.registries.task_registry import TaskRegistry
from DashAI.back.tasks.base_task import BaseTask


class Task1(BaseTask):
    __test__ = False
    name = "Task1"


class Task2(BaseTask):
    name = "Task2"


class Task3(BaseTask):
    name = "Task3"


class NoTask:
    name = "NoTask"


def test__init__empty_tasks():
    task_registry = TaskRegistry(tasks=[])
    assert hasattr(task_registry, "_tasks")
    assert isinstance(task_registry._tasks, dict)
    assert task_registry.tasks == {}


def test__init__bad_tasks_argument():
    with pytest.raises(
        TypeError,
        match="default_tasks should be a list of tasks, got None.",
    ):
        TaskRegistry(tasks=None)


def test__init__with_two_tasks():
    task_registry = TaskRegistry(tasks=[Task1, Task2])
    assert hasattr(task_registry, "_tasks")
    assert isinstance(task_registry._tasks, dict)
    assert task_registry.tasks == {
        "Task1": Task1,
        "Task2": Task2,
    }

    for task in task_registry.tasks:
        assert issubclass(task_registry.tasks[task], BaseTask)


def test_register_task_empty_initial_tasks():
    task_registry = TaskRegistry(tasks=[])
    # register task1
    task_registry.register_task(Task1)
    assert task_registry.tasks == {"Task1": Task1}
    # register task2
    task_registry.register_task(Task2)
    assert task_registry.tasks == {
        "Task1": Task1,
        "Task2": Task2,
    }


def test_register_task_with_inital_task():
    task_registry = TaskRegistry(tasks=[Task1])
    assert hasattr(task_registry, "_tasks")
    assert task_registry.tasks == {"Task1": Task1}

    task_registry.register_task(Task2)
    assert task_registry.tasks == {
        "Task1": Task1,
        "Task2": Task2,
    }

    task_registry.register_task(Task3)
    assert task_registry.tasks == {
        "Task1": Task1,
        "Task2": Task2,
        "Task3": Task3,
    }


def test_try_register_wrong_type():
    task_registry = TaskRegistry(tasks=[])

    with pytest.raises(
        TypeError,
        match=(
            "task should be a subclass of Task, got "
            "<class 'test_task_registry.NoTask'>."
        ),
    ):
        task_registry.register_task(NoTask)
