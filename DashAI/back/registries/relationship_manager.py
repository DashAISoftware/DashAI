from collections import defaultdict
from typing import DefaultDict


class TaskComponentRelationshipManager:
    """Class that implements a relationship registry between tasks and components.

    The registry is a pair of dicts (defaultdicts) that stores the relationships as a
    dictionary where its keys are some class and its values a list of classes that are
    related with the class.

    For example, the `task_to_component_relations` dict contains:

    ```python
    {
        "TabularClassificationTask": ["SVM", "KNN", "CSVDataloader", ...]
    }
    ```

    While its counterpart, the `component_to_task_relations` contains the inverse
    information:

    ```python
    {
        "SVM": ["TabularClassificationTask"],
        "KNN": ["TabularClassificationTask"],
        "CSVDataloader": ["TabularClassificationTask"],
    }
    ```

    Note that the relations are duplicated and hopefully, consistent between them.
    """

    def __init__(self) -> None:
        self._task_to_component_relations: DefaultDict[str, list[str]] = defaultdict(
            list
        )
        self._component_to_task_relations: DefaultDict[str, list[str]] = defaultdict(
            list
        )

    @property
    def task_component_relations(self) -> dict[str, list[str]]:
        return dict(self._task_to_component_relations)

    @task_component_relations.setter
    def task_component_relations(self, _) -> None:
        raise RuntimeError(
            "It is not allowed to set the task_component_relations values directly."
        )

    @task_component_relations.deleter
    def task_component_relations(self, _) -> None:
        raise RuntimeError(
            "It is not allowed to delete the task_component_relations attribute."
        )

    @property
    def component_to_task_relations(self) -> dict[str, list[str]]:
        return dict(self._component_to_task_relations)

    @component_to_task_relations.setter
    def component_to_task_relations(self, _) -> None:
        raise RuntimeError(
            "It is not allowed to set the component_to_task_relations values directly."
        )

    @component_to_task_relations.deleter
    def component_to_task_relations(self, _) -> None:
        raise RuntimeError(
            "It is not allowed to delete the component_to_task_relations attribute."
        )

    def add_relationship(self, component_name: str, task_name: str) -> None:
        if not isinstance(task_name, str):
            raise TypeError(f"task_name should be a string, got {task_name}")
        if not isinstance(component_name, str):
            raise TypeError(f"component_name should be a string, got {component_name}")

        self._task_to_component_relations[task_name].append(component_name)
        self._component_to_task_relations[component_name].append(task_name)

    def get_task_related_components(self, task_name: str) -> list[str]:
        if not isinstance(task_name, str):
            raise TypeError(f"task_name should be a string, got {task_name}")

        if task_name not in self.task_to_component_relations:
            raise ValueError(
                f"task {task_name} does not exist in the task-component "
                "relationship register"
            )

        return self.task_to_component_relations[task_name]

    def get_components_related_tasks(self, component_name: str) -> list[str]:
        if not isinstance(component_name, str):
            raise TypeError(f"component_name should be a string, got {component_name}")

        if component_name not in self.component_to_task_relations:
            raise ValueError(
                f"component {component_name} does not exist in the task-component "
                "relationship register"
            )

        return self.component_to_task_relations[component_name]
