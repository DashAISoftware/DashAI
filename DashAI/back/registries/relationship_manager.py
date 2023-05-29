from collections import defaultdict
from typing import DefaultDict


class RelationshipManager:
    """Class that implements a relationship registry between DashAI components.

    The registry is a pair of dicts (defaultdicts) that stores the relationships as a
    dictionary where its keys are some class and its values a list of classes that are
    related with the class.

    For example, a `_relation`that stores relations between
    "TabularClassificationTask" and "SVM", "KNN" models and "CSVDataloader" loader
    could be:

    ```
    {
        "TabularClassificationTask": ["SVM", "KNN", "CSVDataloader", ...],
        "SVM": ["TabularClassificationTask"],
        "KNN": ["TabularClassificationTask"],
        "CSVDataloader": ["TabularClassificationTask"],

    }
    ```
    Note that the relations are duplicated and hopefully, consistent between them.

    """

    def __init__(self) -> None:
        """Initialize the relationship manager."""
        self._relations: DefaultDict[str, list[str]] = defaultdict(list)

    @property
    def relations(self) -> dict[str, list[str]]:
        return dict(self._relations)

    @relations.setter
    def relations(self, _) -> None:
        raise RuntimeError(
            "It is not allowed to set the task_component_relations values directly."
        )

    @relations.deleter
    def relations(self, _) -> None:
        raise RuntimeError(
            "It is not allowed to delete the task_component_relations attribute."
        )

    def add_relationship(
        self, first_component_id: str, second_component_id: str
    ) -> None:
        """Add a new relation to the relationship manager.

        Note that the relation is bidirectional.

        Parameters
        ----------
        first_component_id : str
            First component id or name.
        second_component_id : str
            Second component id or name.

        Raises
        ------
        TypeError
            If the first_component_id is not a string
        TypeError
            If the second_component_id is not a string
        """
        if not isinstance(first_component_id, str):
            raise TypeError(
                f"first_component_id should be a string, got {first_component_id}"
            )
        if not isinstance(second_component_id, str):
            raise TypeError(
                f"second_component_id should be a string, got {second_component_id}"
            )
        self._relations[first_component_id].append(second_component_id)
        self._relations[second_component_id].append(first_component_id)

    def __contains__(self, component_id: str) -> bool:
        if not isinstance(component_id, str):
            raise TypeError(f"The indexator should be a string, got {component_id}.")

        return component_id in self._relations

    def __getitem__(self, component_id: str) -> list[str]:
        """Obtains all stored relationships from a specific component.

        Raises a ValueError in case that the component does not exist in the manager.

        Parameters
        ----------
        component_id : str
            A component name or id.

        Returns
        -------
        list[str]
            A list with the related components.

        Raises
        ------
        TypeError
            If component_id is not a string
        ValueError
            If component_id does not exists in the relationship manager.
        """
        if not isinstance(component_id, str):
            raise TypeError(f"component_id should be a string, got {component_id}")

        return self._relations[component_id]
