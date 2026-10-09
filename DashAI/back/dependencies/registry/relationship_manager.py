import logging
from collections import defaultdict
from typing import Any

from beartype import beartype
from beartype.typing import DefaultDict, Dict, List

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DEFAULT_RELATION_TYPE = "compatible_components"


class RelationshipManager:
    """Registry of typed relationships between DashAI components.

    Relations are stored as a nested mapping
    ``{component_id: {relation_type: [related_component_id, ...]}}``.
    Each relation is stored bidirectionally and scoped by ``relation_type``
    (for example ``"compatible_components"``, ``"required_credentials"`` or
    ``"optional_credentials"``).
    """

    def __init__(self) -> None:
        """Initialize the relationship manager."""
        self._relations: DefaultDict[str, DefaultDict[str, List[str]]] = defaultdict(
            lambda: defaultdict(list)
        )

    @property
    def relations(self) -> Dict[str, Dict[str, List[str]]]:
        return {
            component_id: dict(relations)
            for component_id, relations in self._relations.items()
        }

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

    @beartype
    def add_relationship(
        self,
        first_component_id: str,
        second_component_id: str,
        relation_type: str = DEFAULT_RELATION_TYPE,
    ) -> None:
        """Add a new bidirectional relation of the given type.

        Parameters
        ----------
        first_component_id : str
            First component id or name.
        second_component_id : str
            Second component id or name.
        relation_type : str
            The relation category, by default ``"compatible_components"``.
        """
        self._relations[first_component_id][relation_type].append(second_component_id)
        self._relations[second_component_id][relation_type].append(first_component_id)

    @beartype
    def remove_relationship(
        self,
        first_component_id: str,
        second_component_id: str,
        relation_type: str = DEFAULT_RELATION_TYPE,
    ) -> None:
        """Remove an existing relation of the given type.

        Parameters
        ----------
        first_component_id : str
            First component id or name.
        second_component_id : str
            Second component id or name.
        relation_type : str
            The relation category, by default ``"compatible_components"``.

        Raises
        ------
        ValueError
            If the relation does not exist.
        """
        try:
            self._relations[first_component_id][relation_type].remove(
                second_component_id
            )
            self._relations[second_component_id][relation_type].remove(
                first_component_id
            )
        except ValueError as e:
            raise ValueError(
                f"Error: Relationship of type '{relation_type}' between "
                f"{first_component_id} and {second_component_id} does not exist "
                f"in the registry. Exception: {e}"
            ) from e

        logger.info(
            f"Components successfully removed from registry:"
            f"{first_component_id}, {second_component_id}"
        )

    @beartype
    def get(
        self, component_id: str, relation_type: str = DEFAULT_RELATION_TYPE
    ) -> List[str]:
        """Return the related component ids of a given type.

        Parameters
        ----------
        component_id : str
            A component name or id.
        relation_type : str
            The relation category, by default ``"compatible_components"``.

        Returns
        -------
        list[str]
            Related component ids, or an empty list if none exist.
        """
        if component_id in self._relations:
            return list(self._relations[component_id].get(relation_type, []))
        return []

    @beartype
    def __contains__(self, component_id: str) -> bool:
        """Indicate if the relation manager contains a component.

        Parameters
        ----------
        component_id : str
            The id of the component to check.

        Returns
        -------
        bool
            True if the component has any relation, False otherwise.
        """
        return component_id in self._relations

    @beartype
    def __getitem__(self, component_id: str) -> Dict[str, List[str]]:
        """Obtain all stored relationships for a component, grouped by type.

        Parameters
        ----------
        component_id : str
            A component name or id.

        Returns
        -------
        dict[str, list[str]]
            Mapping of relation type to related component ids. Empty dict if
            the component is unknown.
        """
        if component_id in self._relations:
            return dict(self._relations[component_id])
        return {}
