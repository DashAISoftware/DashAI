import logging
from typing import Any, Union

from beartype import beartype
from beartype.typing import Dict, List, Type

from DashAI.back.core.utils import MultilingualString
from DashAI.back.dependencies.registry.relationship_manager import RelationshipManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ComponentRegistry:
    """An object that stores all components registered in a execution of DashAI.

    Each object registered is saved as a component dict, which is an abstraction layer
    that stores all relevant component attributes.

    An example of component dict is:

    ```python
    {
        "name": "Component1",  # Component name.
        "type": "ComponentType",  # Component type.
        "class": Component1,  # Component class.
        "configurable_object": False,  # True if the object is a configurable one.
        "schema": {...},  # Configurable object schema if applies.
        "metadata": {...},  # Component metadata if applies.
        "description": "...",  # An object description.
        "display_name": "...",  # A readable label.
        "color": "...",  # A color associated to the component.
        "downloaded": True,  # False until a download-required component is fetched.
    }
    ```

    By default, every method of the registry should return a component dict or a list
    of component dicts.
    """

    @beartype
    def __init__(
        self,
        initial_components: Union[List[type], None] = None,
    ) -> None:
        """Initialize the component registry.

        Parameters
        ----------
        initial_components : Union[List[type], None]
            List with the initial objects to be entered in the registry,
            by default None.

        Raises
        ------
        TypeError
            If initial_components is not a list of types.
        TypeError
            If the task registry is neither none nor an instance of BaseRegistry.
        """
        self._registry: Dict[str, Dict[str, Any]] = {}
        self._relationship_manager = RelationshipManager()

        if initial_components is not None:
            for component in initial_components:
                self.register_component(component)

        # Ensure every component carries the downloaded flag.
        self.seed_download_status()

    @property
    @beartype
    def registry(self) -> Dict[str, Dict[str, Any]]:
        """Obtains the internal registry object.

        Returns
        -------
        Dict[str, Dict[str, Any]]
            Registry dict.
        """
        return self._registry

    @registry.setter
    def registry(self, _: Any) -> None:
        raise RuntimeError("It is not allowed to set the registry values directly.")

    @registry.deleter
    def registry(self, _: Any) -> None:
        raise RuntimeError("It is not allowed to delete the registry list.")

    @beartype
    def __contains__(self, item: str) -> bool:
        """Indicate if some component is in the registry.

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

    @beartype
    def __getitem__(self, item: str) -> Dict[str, Any]:
        """Obtain a component from the registry using an indexer.

        Parameters
        ----------
        item : str
            A string to be used as an indexer.

        Returns
        -------
        Dict[str, type]
            The request component dict.

        Raises
        ------
        TypeError
            If the indexer is not a string.
        KeyError
            If the object does not exist in the registry.
        """
        for base_type_container in self._registry.values():
            if item in base_type_container:
                return base_type_container[item]

        raise KeyError(f"Component '{item}' does not exists in the registry.")

    @beartype
    def _get_base_type(self, new_component: type) -> str:
        # select only base classes ancestors
        component_base_ancestors = [
            ancestor
            for ancestor in new_component.__mro__
            if "Base" in ancestor.__name__
        ]

        base_classes_cantidates = [
            ancestor_cls
            for ancestor_cls in component_base_ancestors
            if hasattr(ancestor_cls, "TYPE")
        ]

        # check if there is only one type candidate.
        if len(base_classes_cantidates) == 0:
            raise TypeError(
                f"Component {new_component.__name__} does not inherit from any DashAI "
                f"base class with a 'TYPE' class attribute. Classes that the component "
                f"extends (MRO): {new_component.__mro__}."
            )
        elif len(base_classes_cantidates) > 1:
            raise TypeError(
                f"Component {new_component.__name__} has more than one base class with "
                f"a 'TYPE' class attribute: "
                f"{[_cls.__name__ for _cls in base_classes_cantidates]}."
            )

        if not hasattr(base_classes_cantidates[0], "TYPE"):
            raise TypeError(
                f"{base_classes_cantidates[0].__name__} "
                "base class has not class attribute TYPE"
            )

        return base_classes_cantidates[0].TYPE

    @staticmethod
    @beartype
    def _collect_compatible_components(component: type) -> List[str]:
        """Collect the union of ``COMPATIBLE_COMPONENTS`` declared along the MRO.

        Each class in the component's MRO contributes only the entries it
        declares itself, so mixins and base classes compose instead of the
        first declaration shadowing the rest (e.g. a task mixin declaring the
        task plus a model base class declaring its supported explainers).

        Parameters
        ----------
        component : type
            The component class to inspect.

        Returns
        -------
        List[str]
            Deduplicated compatible component names in MRO order.
        """
        compatible_components: List[str] = []
        for klass in component.__mro__:
            for entry in vars(klass).get("COMPATIBLE_COMPONENTS", []):
                if entry not in compatible_components:
                    compatible_components.append(entry)
        return compatible_components

    @beartype
    def register_component(self, new_component: Type) -> None:
        """Register a component within the registry.

        Parameters
        ----------
        new_component : Type
            The object to be registred.


        """
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

        _metadata = (
            new_component.get_metadata()
            if hasattr(new_component, "get_metadata")
            else None
        )

        # Format description and display_name as MultilingualString if they are str
        if hasattr(new_component, "DESCRIPTION"):
            description = new_component.DESCRIPTION
            if isinstance(description, str):
                new_component.DESCRIPTION = MultilingualString(en=description)

        if hasattr(new_component, "DISPLAY_NAME"):
            display_name = new_component.DISPLAY_NAME
            if isinstance(display_name, str):
                new_component.DISPLAY_NAME = MultilingualString(en=display_name)

        required_credentials = list(
            getattr(new_component, "REQUIRED_CREDENTIALS", []) or []
        )
        optional_credentials = list(
            getattr(new_component, "OPTIONAL_CREDENTIALS", []) or []
        )

        new_register_component = {
            "name": new_component.__name__,
            "type": base_type,
            "class": new_component,
            "configurable_object": is_configurable_object,
            "schema": new_component.get_schema() if is_configurable_object else None,
            "metadata": _metadata,
            "description": getattr(new_component, "DESCRIPTION", None),
            "display_name": getattr(new_component, "DISPLAY_NAME", None),
            "color": getattr(new_component, "COLOR", None),
            "required_credentials": required_credentials,
            "optional_credentials": optional_credentials,
            "credentials_satisfied": len(required_credentials) == 0,
        }

        if base_type not in self._registry:
            self._registry[base_type] = {new_component.__name__: new_register_component}
        else:
            self._registry[base_type][new_component.__name__] = new_register_component

        self._set_download_status(new_register_component)

        if hasattr(new_component, "COMPATIBLE_COMPONENTS"):
            for compatible_component in self._collect_compatible_components(
                new_component
            ):
                self._relationship_manager.add_relationship(
                    new_component.__name__,
                    compatible_component,
                    "compatible_components",
                )

        for credential_name in required_credentials:
            self._relationship_manager.add_relationship(
                new_component.__name__, credential_name, "required_credentials"
            )

        for credential_name in optional_credentials:
            self._relationship_manager.add_relationship(
                new_component.__name__, credential_name, "optional_credentials"
            )

    def seed_download_status(self) -> None:
        """Populate the ``downloaded`` flag for every registered component.

        Downloadable components are checked via their ``is_downloaded`` method;
        all other components are always considered available.
        """
        for type_dict in self._registry.values():
            for _name, component_dict in type_dict.items():
                self._set_download_status(component_dict)

    def refresh_download_status(self, name: str) -> bool:
        """Recheck a single component's download status and update the registry.

        Parameters
        ----------
        name : str
            The component class name.

        Returns
        -------
        bool
            The reconciled ``downloaded`` value.
        """
        component_dict = self[name]
        return self._set_download_status(component_dict)

    def _set_download_status(self, component_dict: dict) -> bool:
        """Set the ``downloaded`` key on a component dict and return the value.

        Parameters
        ----------
        component_dict : dict
            A registry component dict to update in place.

        Returns
        -------
        bool
            The resolved download status for the component.

        Notes
        -----
        Exceptions from ``is_downloaded()`` are suppressed and treated as
        not-downloaded, so a component may appear not-downloaded without raising.
        """
        component_class = component_dict["class"]
        requires = bool(getattr(component_class, "REQUIRES_DOWNLOAD", False))
        if requires:
            try:
                downloaded = bool(component_class.is_downloaded())
            except Exception:
                downloaded = False
        else:
            downloaded = True
        component_dict["downloaded"] = downloaded
        return downloaded

    @beartype
    def unregister_component(self, component: Type) -> None:
        """Remove a component from the registry.

        Parameters
        ----------
        component : Type
            The object to be registred.


        """
        base_type = self._get_base_type(component)

        try:
            self._registry[base_type].pop(component.__name__)
            logger.info(f"Component removed: {component.__name__}")
        except KeyError as e:
            raise ValueError(
                f"Error: Component named {component.__name__} does not exist "
                f"in the registry. Exception: {e}"
            ) from e

        for compatible_component in self._collect_compatible_components(component):
            self._relationship_manager.remove_relationship(
                component.__name__,
                compatible_component,
                "compatible_components",
            )

        for credential_name in getattr(component, "REQUIRED_CREDENTIALS", []) or []:
            self._relationship_manager.remove_relationship(
                component.__name__, credential_name, "required_credentials"
            )

        for credential_name in getattr(component, "OPTIONAL_CREDENTIALS", []) or []:
            self._relationship_manager.remove_relationship(
                component.__name__, credential_name, "optional_credentials"
            )

    @beartype
    def get_components_by_types(
        self,
        select: Union[str, List[str], None] = None,
        ignore: Union[str, List[str], None] = None,
    ) -> List[Dict[str, Any]]:
        """Obtain all the components dicts according to the indicated types.

        The function allows to select all components of one or several types at the
        same time (through the select parameter) or to ignore one or several
        types (through the ignore parameter).

        In case select and ignore are None, the function returns all registered
        components.

        In all cases, the function return a list of dictionaries describing
        the components.


        Parameters
        ----------
        select : Union[str, List[str], None], optional
            The types of components selected for return, by default None
        ignore : Union[str, List[str], None], optional
            The types of components ignored for return, by default None

        Returns
        -------
        List[Dict[str, Any]]
            A list with the selected components.

        Raises
        ------
        ValueError
            If select and ignore are not None.
        TypeError
            When select provided, if select is not a string o a list of strings.
        TypeError
            When select provided, if some element of select list is not a string.
        ValueError
            When select provided, when a provided type does not exists in the registry.
        TypeError
            When ignore provided, if ignore is not a string o a list of strings.
        TypeError
            When ignore provided, if some element of ignore list is not a string.
        ValueError
            When ignore provided, when a provided type does not exists in the registry.
        """
        if select is not None and ignore is not None:
            raise ValueError(
                "Only select or ignore can be provided, not both at the same time."
            )

        # Case 1: neither select nor ignore was provided.
        if select is None and ignore is None:
            return [
                self.__getitem__(component)
                for component_type in self.registry
                for component in self._registry[component_type]
            ]

        # Case 2: only select is provided.
        if select is not None:
            # check passed select types
            if not isinstance(select, (str, list)):
                raise TypeError(
                    f"Select must be a string or an array of strings, got {select}."
                )
            # cast select into string
            if isinstance(select, str):
                select = [select]

            if len(select) == 0:
                raise ValueError("Select list has not types to select.")

            for idx, component_type in enumerate(select):
                if not isinstance(component_type, str):
                    raise TypeError(
                        f"Select type at position {idx} should be a string, "
                        f"got {component_type}."
                    )
                if component_type not in self._registry:
                    raise ValueError(
                        f"Component type {component_type} does not exist in the "
                        "registry."
                    )

            return [
                self.__getitem__(component)
                for selected_type in select
                for component in self._registry[selected_type]
            ]

        # Case 3: only ignore is provided.
        else:
            # check passed ignore types
            if not isinstance(ignore, (str, list)):
                raise TypeError(
                    f"Ignore must be a string or an array of strings, got {ignore}."
                )
            # cast select into string
            if isinstance(ignore, str):
                ignore = [ignore]

            if len(ignore) == 0:
                raise ValueError("Ignore list has not types to select.")

            # check each type
            for idx, component_type in enumerate(ignore):
                if not isinstance(component_type, str):
                    raise TypeError(
                        f"Ignore type at position {idx} should be a string, got "
                        f"{component_type}."
                    )
                if component_type not in self._registry:
                    raise ValueError(
                        f"Component type {component_type} does not exist in the "
                        "registry."
                    )

            return [
                self.__getitem__(component)
                for component_type in self.registry
                if component_type not in ignore
                for component in self._registry[component_type]
            ]

    @beartype
    def get_child_components(
        self, parent_name: str, recursive: bool = False
    ) -> List[Dict[str, Any]]:
        """Obtain the compoments that inherits from the specified parent component.

        Note that the method will not raise an exception when a non existant parent
        name is passed.

        Parameters
        ----------
        parent_name : str
            Class name of the parent component
        recursive : bool
            If True, search for all child and subchild classes.

        Returns
        -------
        List[Dict[str, Any]]
            List of component dicts that inherits from the parent component.
        """
        selected_components = []
        for type_registry in self._registry.values():
            for component_dict in type_registry.values():
                component_bases = (
                    component_dict["class"].__mro__
                    if recursive
                    else component_dict["class"].__bases__
                )
                component_bases_names = [cls_.__name__ for cls_ in component_bases]

                if parent_name in component_bases_names:
                    selected_components.append(component_dict)

        return selected_components

    @beartype
    def get_related_components(self, component_id: str) -> List[Dict[str, Any]]:
        """Obtain any related component of the given component name.

        If the component has no related components, then the method returns an empty
        list. Related names that are not registered components (e.g. an explainer
        declared by a model but provided by an uninstalled plugin) are skipped.

        Parameters
        ----------
        component_id : str
            A registered component name.

        Returns
        -------
        List[Dict[str, Any]]
            A list with component dicti with all related components.

        Raises
        ------
        KeyError
            If component id does not exists in the registry.
        """
        if not self.__contains__(component_id):
            raise KeyError(
                f"Component '{component_id}' does not exists in the registry."
            )

        return [
            self.__getitem__(related_component_id)
            for related_component_id in self._relationship_manager.get(
                component_id, "compatible_components"
            )
            if self.__contains__(related_component_id)
        ]

    @beartype
    def get_required_credentials(self, component_id: str) -> List[str]:
        """Return the names of credentials a component requires.

        Parameters
        ----------
        component_id : str
            A registered component name.

        Returns
        -------
        List[str]
            Names of required credential components (empty if none).
        """
        return self._relationship_manager.get(component_id, "required_credentials")

    @beartype
    def get_optional_credentials(self, component_id: str) -> List[str]:
        """Return the names of credentials a component can optionally use.

        Parameters
        ----------
        component_id : str
            A registered component name.

        Returns
        -------
        List[str]
            Names of optional credential components (empty if none).
        """
        return self._relationship_manager.get(component_id, "optional_credentials")

    @beartype
    def refresh_credentials_status(
        self,
        statuses: Dict[str, bool],
        only: Union[List[str], None] = None,
    ) -> None:
        """Recompute the ``credentials_satisfied`` flag of components.

        A component is satisfied when every credential in its
        ``required_credentials`` is verified. Components with no required
        credentials are always satisfied.

        Parameters
        ----------
        statuses : Dict[str, bool]
            Mapping of credential component name to verified status.
        only : Union[List[str], None]
            If provided, only these component names are recomputed. If None,
            all components are recomputed.
        """
        for type_registry in self._registry.values():
            for name, component_dict in type_registry.items():
                if only is not None and name not in only:
                    continue
                required = component_dict.get("required_credentials", [])
                component_dict["credentials_satisfied"] = all(
                    statuses.get(credential_name, False) for credential_name in required
                )
