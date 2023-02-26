import pytest

from DashAI.back.models import BaseModel
from DashAI.back.registries import ModelRegistry, TaskRegistry
from DashAI.back.tasks import BaseTask


class Task1(BaseTask):
    name = "Task1"


class Task2(BaseTask):
    name = "Task2"


class Model1ForTask1(BaseModel):
    MODEL = "Model1ForTask1"
    _compatible_tasks = ["Task1"]


class Model2ForTask1(BaseModel):
    MODEL = "Model2ForTask1"
    _compatible_tasks = ["Task1"]


class Model1ForTask2(BaseModel):
    MODEL = "Model1ForTask2"
    _compatible_tasks = ["Task2"]


@pytest.fixture()
def task_registry() -> TaskRegistry:
    return TaskRegistry(tasks=[Task1, Task2])


def test__init__empty_tasks(task_registry: TaskRegistry):
    model_registry = ModelRegistry(task_registry=task_registry, models=[])
    assert hasattr(model_registry, "_models")
    assert hasattr(model_registry, "models")
    assert hasattr(model_registry, "_task_registry")
    assert isinstance(model_registry._models, dict)
    assert isinstance(model_registry.models, dict)
    assert model_registry._models == {}
    assert model_registry._models == model_registry.models


def test__init__bad_model_argument(task_registry: TaskRegistry):
    with pytest.raises(
        TypeError,
        match="task_registry must be an instance of TaskRegistry, got None.",
    ):
        ModelRegistry(task_registry=None, models=[])

    with pytest.raises(
        TypeError,
        match="models must be a list of model classes, got None.",
    ):
        ModelRegistry(task_registry=task_registry, models=None)


def test__init__empty_initial_tasks(task_registry: TaskRegistry):
    model_registry = ModelRegistry(task_registry, models=[])

    # register model1
    model_registry.register_model(Model1ForTask1)
    assert model_registry.models == {"Model1ForTask1": Model1ForTask1}
    assert model_registry._task_registry["Task1"].compatible_models == [Model1ForTask1]
    assert model_registry._task_registry["Task2"].compatible_models == []

    # register model2 and check if it was correctly associated with the task 1
    model_registry.register_model(Model2ForTask1)
    assert model_registry.models == {
        "Model1ForTask1": Model1ForTask1,
        "Model2ForTask1": Model2ForTask1,
    }
    assert model_registry._task_registry["Task1"].compatible_models == [
        Model1ForTask1,
        Model2ForTask1,
    ]
    assert model_registry._task_registry["Task2"].compatible_models == []

    # register model3
    model_registry.register_model(Model1ForTask2)
    assert model_registry.models == {
        "Model1ForTask1": Model1ForTask1,
        "Model2ForTask1": Model2ForTask1,
        "Model1ForTask2": Model1ForTask2,
    }
    assert model_registry._task_registry["Task1"].compatible_models == [
        Model1ForTask1,
        Model2ForTask1,
    ]
    assert model_registry._task_registry["Task2"].compatible_models == [
        Model1ForTask2,
    ]


# def test__init__with_two_models():
#     task_registry = TaskRegistry(tasks=[Task1, Task2])
#     assert hasattr(task_registry, "_tasks")
#     assert isinstance(task_registry._tasks, dict)
#     assert task_registry.tasks == {
#         "Task1": Task1,
#         "Task2": Task2,
#     }

#     for task in task_registry.tasks:
#         assert issubclass(task_registry.tasks[task], BaseTask)


# def test_register_task_with_inital_task():
#     task_registry = TaskRegistry(tasks=[Task1])
#     assert hasattr(task_registry, "_tasks")
#     assert task_registry.tasks == {"Task1": Task1}

#     task_registry.register_task(Task2)
#     assert task_registry.tasks == {
#         "Task1": Task1,
#         "Task2": Task2,
#     }

#     task_registry.register_task(Task3)
#     assert task_registry.tasks == {
#         "Task1": Task1,
#         "Task2": Task2,
#         "Task3": Task3,
#     }


# def test_try_register_wrong_type():
#     task_registry = TaskRegistry(tasks=[])

#     with pytest.raises(
#         TypeError,
#         match=(
#             "task should be a subclass of Task, got "
#             "<class 'test_task_registry.NoTask'>."
#         ),
#     ):
#         task_registry.register_task(NoTask)
#         task_registry.register_task(NoTask)
#         task_registry.register_task(NoTask)
