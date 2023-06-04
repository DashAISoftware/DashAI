from abc import ABC, abstractmethod
from typing import Dict, List, Type, Union


class BaseRegistry(ABC):
    def __init__(
        self,
        initial_components: List[Type],
        task_registry: Union["BaseRegistry", None] = None,
    ) -> None:
        """Initializes the registry.

        Parameters
        ----------
        initial_components : List[Type]
            List with the initial objects to be entered in the registry.
        task_registry : Union[BaseRegistry, None]
            Task register which will allow linking the components with their
            respective tasks, by default None.s

        Raises
        ------
        TypeError
            If initial_components is not a list.
        TypeError
            If the task registry is neither none nor an instance of BaseRegistry.
        """

        if not isinstance(initial_components, list):
            raise TypeError(
                f"initial_components should be a list of {self.registry_for.__name__}"
                f" subclasses, got {initial_components}."
            )
        if task_registry is not None and not isinstance(task_registry, BaseRegistry):
            raise TypeError(
                "task_registry should be a instance of some class that "
                f"extends BaseRegistry, got {task_registry}."
            )

        self._registry: dict[str, type] = {}
        self._task_registry = task_registry

        if self._task_registry is not None:
            # ducktyping from TaskComponentMappingMixin
            self.init_task_component_mapping()

        for component in initial_components:
            self.register_component(component)

    @property
    @abstractmethod
    def registry_for(self) -> type:
        """Base class of the components to be registered in this registry."""
        raise NotImplementedError

    def __contains__(self, item: str) -> bool:
        """Indicates if some component is in the registry.

        Parameters
        ----------
        item : str
            the component name to be checked.

        Returns
        -------
        bool
            True if the component exists in the task registry, False otherwise.
        """
        return item in self.registry

    def __getitem__(self, key: str) -> type:
        """Defines how to get some component from the registry using an indexer.

        Parameters
        ----------
        key : str
            A string to be used as an indexer.

        Returns
        -------
        Type
            The object if it exists in the task registry.

        Raises
        ------
        TypeError
            If the indexer is not a string.
        KeyError
            If the object does not exist in the registry.
        """
        if not isinstance(key, str):
            raise TypeError(f"The indexer should be a string, got {key}.")
        if key not in self.registry:
            raise KeyError(
                f"{key} does not exists in the {self.registry_for.__name__} registry."
            )

        return self.registry[key]

    @property
    def registry(self) -> Dict[str, Type]:
        return self._registry

    @registry.setter
    def registry(self, _) -> None:
        raise RuntimeError("It is not allowed to set the registry values directly.")

    @registry.deleter
    def registry(self, _) -> None:
        raise RuntimeError("It is not allowed to delete the registry list.")

    def register_component(self, new_component: type) -> None:
        """Register a component within the registry.

        Parameters
        ----------
        new_component : Type
            The object to be registred.

        Raises
        ------
        TypeError
            If the provided component is not a class.
        TypeError
            If some task that the component declares compatible does not exist in the
            taskm registry.
        """
        if not isinstance(new_component, type):
            raise TypeError(f"new_component should be a class, got {new_component}.")

        if not issubclass(new_component, self.registry_for):
            raise TypeError(
                f"new_component should be a subclass of {self.registry_for.__name__}, "
                f"got {new_component}."
            )

        if self._task_registry is not None:
            # link a task with the components.
            # it assumes thas if _task_registry, then the registry extended the
            # TaskComponentMappingMixin.
            self.link_task_with_component(new_component)

        # add the model to the registry.
        self._registry[new_component.__name__] = new_component

    def parent_to_components(self, parent_name: str) -> List[str]:
        """Obtain the compoments that inherits from the specified parent component.

        Parameters
        ----------
        parent_name : str
            Class name of the parent component

        Returns
        -------
        List[str]
            List of component that inherits from the parent component.
        """
        selected_components = []
        for component in self._registry.values():
            component_bases = [
                base_class.__name__
                for base_class in component.__bases__
                if base_class.__name__ != "object"
            ]
            if parent_name in component_bases:
                selected_components.append(component)

        return [component.__name__ for component in selected_components]
