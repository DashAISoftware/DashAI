import logging
from typing import List, Union

from fastapi import APIRouter, status
from fastapi.exceptions import HTTPException

from DashAI.back.core.config import name_registry_mapping

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)

router = APIRouter()


@router.get("/")
async def get_components(
    component_type: Union[str, None] = None,
    task_name: Union[str, None] = None,
    component_parent: Union[str, None] = None,
) -> List[dict]:
    """Retrieves components from the register.

    The components returned will depend on the parameters of the request.
    If all parameters are None, then the method will return all registered components.

    Parameters
    ----------
    component_type : Union[str, None], optional
        If specified, the function will return only the components belonging to that
        component type (e.g., task, model, dataloader, etc...), by default None.
    task_name : Union[str, None], optional
        If specified, the function will return only the components related with
        the task (e.g., TabularClassification, Translation), by default None.
    component_parent : Union[str, None], optional
        If specified, the function will return only the components that inherit from the
        indicated component (e.g., ScikitLearnLikeModel), by default None.

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

    # when component type is not none, check if it exists in the registry.
    if component_type is not None and component_type not in name_registry_mapping:
        raise HTTPException(
            status_code=422,
            detail=f"component_type {component_type} does not exist in the registry.",
        )

    # when task_name is not none, check if it exists in the registry.
    if task_name is not None and task_name not in name_registry_mapping["task"]:
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
            for component_name, component_class in registry._registry.items()
        }

    # 2. select the task related components and filter from the initial list
    if task_name is not None:
        task_related_components = []
        for component_type in name_registry_mapping:
            if component_type != "task":
                for component_name in name_registry_mapping[
                    component_type
                ].task_to_components(task_name):
                    task_related_components.append(component_name)

        # filter
        selected_components = {
            component_name: component_class
            for component_name, component_class in selected_components.items()
            if component_name in task_related_components
        }

    #  3. get parent component
    if component_parent is not None:
        child_components = [
            component_class
            for component_type in name_registry_mapping
            for component_class in name_registry_mapping[
                component_type
            ].parent_to_components(component_parent)
        ]

        # filter
        selected_components = {
            component_name: component_class
            for component_name, component_class in selected_components.items()
            if component_name in child_components
        }

    return [component.get_schema() for component in selected_components.values()]


@router.get("/{id}/")
def get_component_by_id(id: str) -> dict:
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
            return registry[id].get_schema()

    raise HTTPException(
        status_code=404, detail=f"Component {id} not found in the registry."
    )


@router.post("/", status_code=status.HTTP_201_CREATED)
async def upload_component():
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Method not implemented"
    )


@router.delete("/")
async def delete_component():
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Method not implemented"
    )


@router.patch("/")
async def update_component():
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Method not implemented"
    )
