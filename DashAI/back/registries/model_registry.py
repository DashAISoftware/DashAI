from typing import List, Type, Union

from DashAI.back.models.base_model import BaseModel
from DashAI.back.registries.task_registry import TaskRegistry
from DashAI.back.tasks.base_task import BaseTask


class ModelRegistry:
    def __init__(
        self,
        task_registry: TaskRegistry,
        models: Union[List[Type[BaseModel]], None],
    ) -> None:
        self._models: dict[str, Type[BaseModel]] = {}
        self._task_registry = task_registry

        # if default tasks were provided, add them to the register
        if models is not None:
            for default_model in models:
                self.register_model(default_model)

    @property
    def tasks(self) -> List[Type[BaseTask]]:
        return self.tasks

    @tasks.setter
    def tasks(self, _) -> None:
        raise RuntimeError("It is not allowed to set the task values directly.")

    @tasks.deleter
    def tasks(self, _) -> None:
        raise RuntimeError("It is not allowed to delete the task list.")

    def register_model(self, model: Type[BaseModel]) -> None:
        """Register a model in the model registry.
        Parameters
        ----------
        model : Type[BaseModel]
            Some model (a class that extends BaseModel)
        Raises
        ------
        TypeError
            If the provided object is not a subclass of BaseModel.
        ValueError
            If a task that the model declares compatible does not exist in the task
            registry.
        """
        if not isinstance(model, type):
            raise TypeError(f"model should be a class, got {model}.")

        # TODO: Fix this later
        # if not issubclass(model, BaseTask):
        #     raise TypeError(
        #         f"model should be a subclass of {BaseModel.__class__.__name__}, "
        #         f"got {model}"
        #     )

        compatible_tasks: list[str] = model._compatible_tasks

        # register the model in each compatible tasks.
        for task_name in compatible_tasks:
            # check if the task exists in the registry.
            if task_name not in self._task_registry._tasks:
                raise ValueError(
                    f"Error while trying to register {model.name} into {task_name}: "
                    f"{task_name} does not exists in the task registry."
                )
            # add compatible model.
            current_task = self._task_registry._tasks[task_name]
            current_task.add_compatible_model(self=current_task, model=model)

        # add the model to the registry.
        # self._models.append(model)
        self._models[model.MODEL] = model
