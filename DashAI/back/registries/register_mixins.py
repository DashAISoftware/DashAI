from collections import defaultdict
from typing import List


class TaskComponentMappingMixin:
    """Mixin that allows relationships between tasks and components in the registry.

    The mapping is simply a dictionary (stored in the task_component_mapping attribute),
    whose keys are the tasks and its values are lists with their associated components.

    The mapping is a defaultdict, which allows new tasks to be dynamically added at
    runtime.

    Upon initialization, the mapping generates a key for each task registered in the
    task registry.
    """

    def init_task_component_mapping(self) -> None:
        """Initialize the mapping between tasks and components."""
        # uses defaultdict to be capable of change the task mapping in the runtime.
        self.task_component_mapping: dict[str, list[str]] = defaultdict(list)

        # initialize the mapping using the already registered tasks.
        for task in self._task_registry.registry:
            self.task_component_mapping[task] = []

    def link_task_with_component(self, new_component: type) -> None:
        """Associates a component with one or more tasks.

        The association occurs within the internal mapping of the object sotred in
        the task_component_mapping attribute.

        Parameters
        ----------
        new_component : Type
            The new component that is going to be associated with its compatible tasks.

        Raises
        ------
        AttributeError
            If the new component does not have attribute _compatible_tasks.
        TypeError
            If _compatible_tasks is not a list.
        ValueError
            If _compatible_tasks does not specify any compatible task.
        KeyError
            If a compatible task does not exist in the task registry.
        """
        # check if new_component has _compatible_tasks class attribute.
        if not hasattr(new_component, "_compatible_tasks"):
            raise AttributeError(
                f"Component {new_component.__name__} has no _compatible_tasks "
                "attribute."
            )

        # check if new_component's _compatible_tasks is a list.
        if not isinstance(new_component._compatible_tasks, list):
            raise TypeError(
                f"Component {new_component.__name__} _compatible_tasks should be a "
                f"list, got {new_component._compatible_tasks} "
            )

        compatible_tasks: list[str] = new_component._compatible_tasks

        # check if the compatible tasks are no a empty list.
        if len(compatible_tasks) == 0:
            raise ValueError(
                f"Component {new_component.__name__} has no associated tasks."
            )

        for compatible_task in compatible_tasks:
            # check if the task exists in the task registry.
            if compatible_task not in self._task_registry:
                raise KeyError(
                    f"Error when trying to associate component {new_component.__name__}"
                    f" with its compatible tasks: task {compatible_task} does not "
                    "exist in the task registry."
                )

            self.task_component_mapping[compatible_task].append(new_component.__name__)

    def task_to_components(self, task_name: str) -> List[str]:
        """Obtain the compatible components with the specified task.

        Parameters
        ----------
        task_name : str
            Class name of the task

        Returns
        -------
        List[str]
            List of component class names supported by the task.

        Raises
        ------
        KeyError
            If the task does not exists in the mapping.
        """
        if task_name not in self.task_component_mapping:
            raise KeyError(
                f"{task_name} does not exists in {self.__class__.__name__}"
                " task_component_mapping."
            )

        return self.task_component_mapping[task_name]

    def component_to_tasks(self, component_name: str) -> List[str]:
        """Obtain the compatible tasks with the specified component.

        Parameters
        ----------
        component_name : str
            Class name of the component

        Returns
        -------
        List[str]
            List of task class names supported by the component.
        """
        # check if the component exists in the registry
        component_cls = self.__getitem__(component_name)
        return component_cls._compatible_tasks
