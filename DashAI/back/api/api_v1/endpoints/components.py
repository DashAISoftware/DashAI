import logging
from typing import Type

from fastapi import APIRouter, status
from fastapi.exceptions import HTTPException

from DashAI.back.core.config import name_registry_mapping
from DashAI.back.registries.base_registry import BaseRegistry

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)

router = APIRouter()


@router.get("/")
async def get_components(
    id: str | None = None,
    component_type: str | None = None,
    task_name: str | None = None,
    component_parent: str | None = None,
) -> list[dict]:
    """Getter that handles component retrieval.

    The components returned will depend on the parameters of the request.
    However, they have order of precedence, which is detailed below:

    1. If id is provided, the function tries to return a list with the requested
       component.
    2. If at least one query parameter is not None, then, execute the query and then
       return the selected components.
    3. In any other case, return all the components.

    Parameters
    ----------
    id : str | None, optional
        _description_, by default None
    component_type : str | None, optional
        _description_, by default None
    task_name : str | None, optional
        _description_, by default None
    component_parent : str | None, optional
        _description_, by default None

    Returns
    -------
    list[dict]
        A list with the selected component schemas.

    Raises
    ------
    HTTPException
        If component_type does not exist in the registry
    HTTPException
        If task_name does not exist in the registry
    """

    # if some id is provided, then return the selected component
    if id is not None:
        selected_components = get_component_by_id(id)

    # when at least one query param is not none, execute the query
    elif any([component_type, task_name, component_parent]):
        selected_components = query_components(
            component_type,
            task_name,
            component_parent,
        )

    # if all query params are None, return everything
    else:
        selected_components = get_all_components(name_registry_mapping)

    # convert classes to schemas and return.
    return [component.get_schema() for component in selected_components]


def get_component_by_id(id: str) -> list[Type]:
    """Return a component using its id.

    Parameters
    ----------
    id : str
        A component identificator

    Returns
    -------
    list[Type]
        A list containing the retrieved component class.

    Raises
    ------
    HTTPException
        If the id does not exists in the registry.
    """
    for registry in name_registry_mapping.values():
        if id in registry:
            return [registry[id]]

    raise HTTPException(
        status_code=404, detail=f"Component {id} not found in the registry."
    )


def query_components(
    component_type: str, task_name: str, component_parent: str
) -> list[Type]:
    # when component type is not none, check if it exists in the registry.
    if component_type is not None and component_type not in name_registry_mapping:
        raise HTTPException(
            status_code=422,
            detail=f"component_type {component_type} does not exist in the registry.",
        )

    # when task_name is not none, check if it exists in the registry.
    if task_name is not None and task_name not in name_registry_mapping["tasks"]:
        raise HTTPException(
            status_code=422,
            detail=f"task_name {task_name} does not exist in the registry.",
        )

    # 1. obtain all components from the selected registry/registries
    if component_type is not None:
        selected_components = name_registry_mapping[component_type].registry
    else:
        selected_components = {
            component_name: component_class
            for registry in name_registry_mapping.values()
            for component_name, component_class in registry
        }

    # 2. select the task related components and filter from the initial list
    if task_name is not None:
        if component_type is not None:
            task_related_components = name_registry_mapping[
                component_type
            ].task_to_components(task_name)

        else:
            task_related_components = [
                name_registry_mapping[component_type].task_to_components(task_name)
                for component_type in name_registry_mapping
                if component_type != "BaseTask"
            ]

        # filter
        selected_components = selected_components = {
            component_name: component_class
            for component_name, component_class in selected_components
            if component_name in task_related_components
        }

    #  3. get parent component
    if component_parent is not None:
        if component_type is not None:
            task_related_components = name_registry_mapping[
                component_type
            ].parent_to_components(component_parent)

        else:
            task_related_components = [
                name_registry_mapping[component_type].parent_to_components(task_name)
                for component_type in name_registry_mapping
            ]

        # filter
        selected_components = selected_components = {
            component_name: component_class
            for component_name, component_class in selected_components
            if component_name in task_related_components
        }

    return selected_components


def get_all_components(name_registry_mapping: dict[str, BaseRegistry]) -> list[dict]:
    """Return all the components included in the registry.

    Parameters
    ----------
    name_registry_mapping : dict[str, BaseRegistry]
        A mapping between some component type name and the registries.

    Returns
    -------
    list[dict]
        A list with component schemas.
    """
    return [
        component
        for registry in name_registry_mapping.values()
        for component in registry.registry.values()
    ]


@router.post("/", status_code=status.HTTP_201_CREATED)
async def upload_component():
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Method not implemented"
    )


@router.delete("/")
async def defete_component():
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Method not implemented"
    )


@router.patch("/")
async def update_component():
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Method not implemented"
    )
