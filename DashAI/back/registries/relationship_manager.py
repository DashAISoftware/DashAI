from collections import defaultdict
from typing import Any, DefaultDict, Dict, List


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
        "TabularClassificationTask": ["SVC", "KNN", "CSVDataloader", ...],
        "SVC": ["TabularClassificationTask"],
        "KNN": ["TabularClassificationTask"],
        "CSVDataloader": ["TabularClassificationTask"],

    }
    ```
    Note that the relations are duplicated and hopefully, consistent between them.

    """

    def __init__(self) -> None:
        """Initialize the relationship manager."""
        self._relations: DefaultDict[str, List[str]] = defaultdict(list)

    @property
    def relations(self) -> Dict[str, List[str]]:
        return dict(self._relations)

    @relations.setter
    def relations(self, _: Any) -> None:
        raise RuntimeError(
            "It is not allowed to set the task_component_relations values directly."
        )

    @relations.deleter
    def relations(self, _: Any) -> None:
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
        """Indicate if the relation manager contains a relationship.

        Parameters
        ----------
        component_id : str
            The id of the component to be checked if a relationship exists or not.

        Returns
        -------
        bool
            True if the relation exists, False otherwise.
        """
        if not isinstance(component_id, str):
            raise TypeError(f"The indexator should be a string, got {component_id}.")

        return component_id in self._relations

    def __getitem__(self, component_id: str) -> List[str]:
        """Obtain all stored relationships from a specific component.

        Return an empty list if the component id does not exists in the relationship
        manager.

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
        """
        if not isinstance(component_id, str):
            raise TypeError(f"component_id should be a string, got {component_id}")

        if component_id in self._relations:
            return self._relations[component_id]

        return []
