"""Task Registry implementation."""
from typing import List, Type

from DashAI.back.tasks.base_task import BaseTask


class TaskRegistry:
    """Centralized registry that focuses on managing the available tasks for DashAI."""

    def __init__(self, tasks: List[Type[BaseTask]]) -> None:
        """Instantiate a task registry.

        Parameters
        ----------
        tasks : List[Type[BaseTask]]
            List with the tasks that are added when the registry is instantiated.

        Raises
        ------
        TypeError
            If tasks is not a list.
        """
        self._tasks: dict[str, Type[BaseTask]] = {}

        if not isinstance(tasks, list):
            raise TypeError(f"tasks should be a list of tasks, got {tasks}.")

        for task in tasks:
            self.register_task(task)

    @property
    def tasks(self) -> List[Type[BaseTask]]:
        """Task getter.

        Returns
        -------
        list[Type[BaseTask]]
            The task registry.
        """
        return self._tasks

    @tasks.setter
    def tasks(self, _) -> None:
        raise RuntimeError("It is not allowed to set the task values directly.")

    @tasks.deleter
    def tasks(self, _) -> None:
        raise RuntimeError("It is not allowed to delete the task list.")

    def __getitem__(self, key: str) -> Type[BaseTask]:
        """Defines how to get some task from the task registry using an indexer.

        Parameters
        ----------
        key : str
            A string to be used as an indexer.

        Returns
        -------
        Type[BaseTask]
            The task if it exists in the task registry.

        Raises
        ------
        TypeError
            If the indexer is not a string.
        KeyError
            If the task does not exist in the registry.
        """
        if not isinstance(key, str):
            raise TypeError(
                f"the indexer must be a string with the name of some task, got {key}."
            )
        if key not in self.tasks:
            raise KeyError(f"the task {key} is not registered in the task registry.")

        return self.tasks[key]

    def __contains__(self, item: str) -> bool:
        """Indicates if some task is in the task registry.

        Parameters
        ----------
        item : str
            the task name to be checked.

        Returns
        -------
        bool
            True if the task exists in the task registry, False otherwise.
        """
        return item in self.tasks

    def register_task(self, task: Type[BaseTask]) -> None:
        """Register a task in the task registry.

        Parameters
        ----------
        task : Type[BaseTask]
            Some task (a class that implements BaseTask).

        Raises
        ------
        TypeError
            If the provided object is not a class.
        TypeError
            If the provided class is not a subclass of task.
        ValueError
            If the provided task already exists in the task registry.
        """
        if not isinstance(task, type):
            raise TypeError(f"task should be a class, got {task}.")

        if not issubclass(task, BaseTask):
            raise TypeError(f"task should be a subclass of Task, got {task}.")

        if task.name in self._tasks:
            raise ValueError(f"the task {task.name} already exists in the registry.")

        self._tasks[task.name] = task
