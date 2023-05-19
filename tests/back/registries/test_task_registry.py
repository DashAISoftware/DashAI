import pytest

from DashAI.back.registries import BaseRegistry, TaskRegistry


def test_task_registry_init__(tasks: tuple[type]):
    Task1, _, _ = tasks  # noqa: N806

    task_registry = TaskRegistry(initial_components=[Task1])

    assert isinstance(task_registry, BaseRegistry)
    assert isinstance(task_registry, TaskRegistry)

    # check initial task
    assert "Task1" in task_registry
    assert task_registry["Task1"] == Task1
    assert task_registry.registry == {"Task1": Task1}


def test_task_registry_register_component(tasks: tuple[type]):
    Task1, Task2, _ = tasks  # noqa: N806
    task_registry = TaskRegistry(initial_components=[Task1])

    # check register component
    task_registry.register_component(Task2)
    assert "Task2" in task_registry
    assert task_registry["Task2"] == Task2
    assert task_registry.registry == {"Task1": Task1, "Task2": Task2}


def test_task_registry_register_wrong_type(tasks: tuple[type]):
    Task1, _, NoTask = tasks  # noqa: N806
    task_registry = TaskRegistry(initial_components=[Task1])

    with pytest.raises(
        TypeError,
        match=(
            r"new_component should be a subclass of BaseTask, got "
            r"<class 'tests.back.registries.conftest.tasks.<locals>.NoTask'>."
        ),
    ):
        task_registry.register_component(NoTask)
