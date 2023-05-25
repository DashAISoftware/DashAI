from DashAI.back.registries.relationship_manager import RelationshipManager


class Registry:
    """An object that stores all components registered in a execution of DashAI."""

    def __init__(
        self,
        initial_components: list[type] | None = None,
    ) -> None:
        """Initializes the registry.

        Parameters
        ----------
        initial_components : List[Type]
            List with the initial objects to be entered in the registry,
            by default None.

        Raises
        ------
        TypeError
            If initial_components is not a list of types.
        TypeError
            If the task registry is neither none nor an instance of BaseRegistry.
        """

        if not isinstance(initial_components, list | type(None)):
            raise TypeError(
                f"initial_components should be a list of component classes or None, "
                f"got {initial_components}."
            )

        self._registry: dict[str, dict[str, type]] = {}
        self._relationship_manager = RelationshipManager()

        if initial_components is not None:
            for component in initial_components:
                self.register_component(component)

    @property
    def registry(self) -> dict[str, dict[str, type]]:
        return self._registry

    @registry.setter
    def registry(self, _) -> None:
        raise RuntimeError("It is not allowed to set the registry values directly.")

    @registry.deleter
    def registry(self, _) -> None:
        raise RuntimeError("It is not allowed to delete the registry list.")

    def __contains__(self, item: str) -> bool:
        """Indicates if some component is in the registry.

        Parameters
        ----------
        item : str
            The component name to be searched.

        Returns
        -------
        bool
            True if the component exists in the task registry, False otherwise.
        """
        for base_type_container in self._registry.values():
            if item in base_type_container:
                return True
        return False

    def __getitem__(self, key: str) -> type:
        """Obtains a component from the registry using an indexer.

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

        for base_type_container in self._registry.values():
            if key in base_type_container:
                return base_type_container[key]

        raise KeyError(f"{key} does not exists in the registry.")

    def _get_base_type(self, new_component: type) -> str:
        # select only base classes ancestors
        component_base_ancestors = [
            ancestor
            for ancestor in new_component.__mro__
            if "Base" in ancestor.__name__
        ]

        type_cantidates = [
            ancestor_cls.TYPE
            for ancestor_cls in component_base_ancestors
            if hasattr(ancestor_cls, "TYPE")
        ]

        # check if there is only one type candidate.
        if len(type_cantidates) == 0:
            raise TypeError(
                f"Component {new_component.__name__} does not a DashAI base class with "
                f"a 'TYPE' class attribute. Classes that the component extends (MRO): "
                f"{new_component.__mro__}"
            )
        elif len(type_cantidates) > 1:
            raise TypeError(
                f"Component {new_component.__name__} has more than one base class with "
                f"a 'TYPE' class attribute. Classes that the component extends (MRO): "
                f"{new_component.__mro__}"
            )

        return type_cantidates[0]

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
            raise TypeError(
                f'new_component "{new_component}" should be a class, '
                f"got {type(new_component)}."
            )

        base_type = self._get_base_type(new_component)

        is_configurable_object = "ConfigObject" in [
            _class.__name__ for _class in new_component.__mro__
        ]

        if is_configurable_object and not hasattr(new_component, "get_schema"):
            raise TypeError(
                f"The component {new_component.__name__} does not implement "
                '"get_schema" method although it was declared as a configurable '
                "object."
            )

        new_register_component = {
            "type": base_type,
            "class": new_component,
            "configurable_object": is_configurable_object,
            "schema": new_component.get_schema() if is_configurable_object else None,
        }

        if base_type not in self._registry:
            self._registry[base_type] = {new_component.__name__: new_register_component}
        else:
            self._registry[base_type][new_component.__name__] = new_register_component

        if hasattr(new_component, "_compatible_tasks"):
            for compatible_task in new_component._compatible_tasks:
                self._relationship_manager.add_relationship(
                    new_component.__name__,
                    compatible_task,
                )
