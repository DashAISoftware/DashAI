from typing import List, Type

from DashAI.back.tasks.base_task import BaseTask


class TaskRegistry:
    def __init__(self, tasks: List[Type[BaseTask]]) -> None:
        self._tasks: dict[str, Type[BaseTask]] = {}

        if not isinstance(tasks, list):
            raise TypeError(
                f"default_tasks should be a list of tasks, got {type(tasks)}"
            )

        for default_task in tasks:
            self.register_task(default_task)

    @property
    def tasks(self) -> List[Type[BaseTask]]:
        """Task getter.
        Returns
        -------
        list[Type[BaseTask]]
            The task registry.
        """
        return self.tasks

    @tasks.setter
    def tasks(self, _) -> None:
        raise RuntimeError("It is not allowed to set the task values directly.")

    @tasks.deleter
    def tasks(self, _) -> None:
        raise RuntimeError("It is not allowed to delete the task list.")

    def register_task(self, task: Type[BaseTask]) -> None:
        """Register a task in the task registry.
        Parameters
        ----------
        task : Type[BaseTask]
            Some class that represent a task.
        Raises
        ------
        TypeError
            If the provided object is not a class.
        TypeError
            If the provided class is not a subclass of task.
        """
        if not isinstance(task, type):
            raise TypeError(f"task should be a class, got {task}.")

        if not issubclass(task, BaseTask):
            raise TypeError(f"task should be a subclass of Task, got {task}")

        if task.name in self._tasks:
            raise ValueError(f"the task {task.name} already exists in the registry.")

        self._tasks[task.name] = task
        self._tasks[task.name] = task
