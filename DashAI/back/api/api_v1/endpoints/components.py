"""Component API module."""
import logging
from typing import Annotated, Any

from fastapi import APIRouter, Query, status
from fastapi.exceptions import HTTPException

from DashAI.back.core.config import component_registry

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)

router = APIRouter()


def _intersect_component_lists(
    previous_selected_components: dict[str, dict[str, Any]],
    component_list: dict[str, dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    selected_components = {
        component_dict["name"]: component_dict
        for component_dict in component_list
        if component_dict["name"] in previous_selected_components
    }
    return selected_components


def _delete_class(component_dict: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in component_dict.items() if key != "class"}


@router.get("/")
async def get_components(
    select_types: Annotated[list[str] | None, Query()] = None,
    ignore_types: Annotated[list[str] | None, Query()] = None,
    related_component: str | None = None,
    component_parent: str | None = None,
) -> list[dict]:
    """Retrieve components from the register according to the provided parameters.

    When all parameters are None, the method return all registered components.
    If more than one parameter is specified, then the method returns the intersection
    between the retrived components.

    The components returned will depend on the parameters of the request.
    If all parameters are None, then the method returns all registered components.

    Parameters
    ----------
    select_types: Annotated[list[str] | None, Query()], optional
        If specified, the function return only the components that extend the
        provided types (e.g., task, model, dataloader, etc...).
        If None, the method returns all components in the registry, by default None.
    ignore_types: Annotated[list[str] | None, Query()], optional
        If specified, the function return every components that is not that extend
        the provided types (e.g., task, model, dataloader, etc...).
        If None, the method returns all components in the registry, by default None.
    related_component : str | None, optional
        If specified, the function return only the components related with
        the specified compatible component, (usually some task. as
        TabularClassification, Translation, etc.), by default None.
    component_parent : str | None, optional
        If specified, the function return only the components that inheirts the
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
    # when select_type is not none, check if it exists in the registry.
    if select_types is not None:
        for select_type in select_types:
            if select_type not in component_registry._registry:
                raise HTTPException(
                    status_code=422,
                    detail=(
                        f"Select type '{select_type}' does not exist in the registry. "
                        f"Available types: {list(component_registry._registry.keys())}."
                    ),
                )

    # when ignore_type is not none, check if it exists in the registry.
    if ignore_types is not None:
        for ignore_type in ignore_types:
            if ignore_type not in component_registry._registry:
                raise HTTPException(
                    status_code=422,
                    detail=(
                        f"Ignore type '{ignore_type}' does not exist in the registry. "
                        f"Available types: {list(component_registry._registry.keys())}."
                    ),
                )

    # when task_name is not none, check if it exists in the registry.
    if related_component is not None and related_component not in component_registry:
        raise HTTPException(
            status_code=422,
            detail=(
                f"Related component {related_component} does not exist in "
                "the registry."
            ),
        )

    # 1. obtain all components from the selected registry/registries
    # if none, get_components_by_type returns all components.
    selected_components = {
        component_dict["name"]: component_dict
        for component_dict in component_registry.get_components_by_types(
            select=select_types
        )
    }

    # 2. ignore the requested types
    if ignore_types is not None:
        selected_components = _intersect_component_lists(
            selected_components,
            component_registry.get_components_by_types(ignore=ignore_types),
        )

    # 3. select only the task related components
    if related_component is not None:
        selected_components = _intersect_component_lists(
            selected_components,
            component_registry.get_related_components(related_component),
        )

    # 4. filter if component parent was specified.
    if component_parent is not None:
        selected_components = _intersect_component_lists(
            selected_components,
            component_registry.get_child_components(component_parent, recursive=True),
        )

    return [
        _delete_class(component_dict) for component_dict in selected_components.values()
    ]


@router.get("/{id}/")
def get_component_by_id(id: str) -> dict:
    """Return an specific component using its id (the id is the component class name).

    Parameters
    ----------
    id : str
        A component identificator

    Returns
    -------
    dict
        The retrieved component dict.

    Raises
    ------
    HTTPException
        If the id does not exists in the registry.
    """
    if id not in component_registry:
        raise HTTPException(
            status_code=404, detail=f"Component {id} not found in the registry."
        )
    return _delete_class(component_registry[id])


@router.post("/", status_code=status.HTTP_201_CREATED)
async def upload_component():
    """Placeholder method for component creation.

    Raises
    ------
    HTTPException
        Always raises exception as it was intentionally not implemented.
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Method not implemented"
    )


@router.delete("/")
async def delete_component():
    """Placeholder method for component delete.

    Raises
    ------
    HTTPException
        Always raises exception as it was intentionally not implemented.
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Method not implemented"
    )


@router.patch("/")
async def update_component():
    """Placeholder for component update.

    Raises
    ------
    HTTPException
        Always raises exception as it was intentionally not implemented.
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Method not implemented"
    )
