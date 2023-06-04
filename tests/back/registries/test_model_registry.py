from typing import List, Type

import pytest

from DashAI.back.models import BaseModel
from DashAI.back.registries import ModelRegistry, TaskRegistry
from DashAI.back.tasks import BaseTask


@pytest.fixture()
def classes():
    class Task1(BaseTask):
        ...

    class Model1(BaseModel):
        _compatible_tasks = ["Task1"]

    class Model2(BaseModel):
        _compatible_tasks = ["Task1"]

    class ModelNonExistantTask(BaseModel):
        _compatible_tasks = ["Task2"]

    return Task1, Model1, Model2, ModelNonExistantTask


def test_model_registry_initial_components(classes: List[Type]):
    Task1, Model1, _, _ = classes
    task_registry = TaskRegistry(initial_components=[Task1])
    model_registry = ModelRegistry(
        initial_components=[Model1],
        task_registry=task_registry,
    )

    # check if the model was added to the registry.
    assert "Model1" in model_registry
    assert model_registry.registry == {"Model1": Model1}

    # check if the model was successfuly linked in the task compatible components.
    assert model_registry.task_component_mapping == {"Task1": ["Model1"]}


def test_model_registry_register_component(classes: List[Type]):
    Task1, Model1, Model2, _ = classes

    task_registry = TaskRegistry(initial_components=[Task1])
    # initial registry with one model
    model_registry = ModelRegistry(
        initial_components=[Model1],
        task_registry=task_registry,
    )

    # add Model2 using register_component and check if it was added correctly.
    model_registry.register_component(Model2)
    assert "Model1" in model_registry
    assert "Model2" in model_registry
    assert model_registry.registry == {"Model1": Model1, "Model2": Model2}

    # check if Model2 was successfuly linked in the task compatible components.

    assert model_registry.task_component_mapping == {"Task1": ["Model1", "Model2"]}


def test_model_registry_non_existant_class(classes: List[Type]):
    Task1, _, _, ModelNonExistantTask = classes
    task_registry = TaskRegistry(initial_components=[Task1])
    with pytest.raises(
        KeyError,
        match=(
            r"Error when trying to associate component ModelNonExistantTask with "
            r"its compatible tasks: task Task2 does not exist in the task registry."
        ),
    ):
        ModelRegistry(
            initial_components=[ModelNonExistantTask],
            task_registry=task_registry,
        )
