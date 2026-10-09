"""Component API module."""

import logging
from typing import TYPE_CHECKING, Any, Dict, List, Union

from fastapi import APIRouter, Depends, Header, Query, Response, status
from fastapi.exceptions import HTTPException
from fastapi.responses import StreamingResponse
from kink import di, inject
from pydantic import BaseModel
from typing_extensions import Annotated

from DashAI.back.core.utils import MultilingualString, localize

if TYPE_CHECKING:
    from DashAI.back.dependencies.registry import ComponentRegistry

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)

router = APIRouter()


def _intersect_component_lists(
    previous_selected_components: Dict[str, Dict[str, Any]],
    component_list: List[Dict[str, Any]],
) -> Dict[str, Dict[str, Any]]:
    selected_components = {
        component_dict["name"]: component_dict
        for component_dict in component_list
        if component_dict["name"] in previous_selected_components
    }
    return selected_components


def _delete_class(component_dict: Dict[str, Any]) -> Dict[str, Any]:
    return {key: value for key, value in component_dict.items() if key != "class"}


@router.get("/")
@inject
async def get_components(
    select_types: Annotated[Union[List[str], None], Query()] = None,
    ignore_types: Annotated[Union[List[str], None], Query()] = None,
    accept_language: str | None = Header(default=None),
    related_component: Union[str, None] = None,
    component_parent: Union[str, None] = None,
    has_related_of_type: Union[str, None] = None,
    component_registry: "ComponentRegistry" = Depends(lambda: di["component_registry"]),
) -> List[Dict[str, Any]]:
    """Retrieve components from the register according to the provided parameters.

    When all parameters are None, the method return all registered components.
    If more than one parameter is specified, then the method returns the intersection
    between the retrived components.

    The components returned will depend on the parameters of the request.
    If all parameters are None, then the method returns all registered components.

    Parameters
    ----------
    select_types: Annotated[Union[List[str], None], Query()], optional
        If specified, the function return only the components that extend the
        provided types (e.g., task, model, dataloader, etc...).
        If None, the method returns all components in the registry, by default None.
    ignore_types: Annotated[Union[List[str], None], Query()], optional
        If specified, the function return every components that is not that extend
        the provided types (e.g., task, model, dataloader, etc...).
        If None, the method returns all components in the registry, by default None.
    accept_language: str | None = Header(default=None)
        The 'Accept-Language' header from the request to localize multilingual
        strings in the component schemas, by default None.
    related_component : Union[str , None], optional
        If specified, the function return only the components related with
        the specified compatible component, (usually some task. as
        TabularClassification, Translation, etc.), by default None.
    component_parent : Union[str , None], optional
        If specified, the function return only the components that inheirts the
        indicated component (e.g., ScikitLearnLikeModel), by default None.
    has_related_of_type : Union[str, None], optional
        If specified, the function returns only components that have at least one
        related component of the specified type (e.g., "Model"). This is useful for
        filtering tasks that have associated models, by default None.
    component_registry: ComponentRegistry
        Registry that provides metadata and class references for the
        components available in DashAI.

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
                f"Related component {related_component} does not exist in the registry."
            ),
        )

    # When has_related_type is not none, check if it exists in the registry.
    if (
        has_related_of_type is not None
        and has_related_of_type not in component_registry._registry
    ):
        raise HTTPException(
            status_code=422,
            detail=(
                f"Type '{has_related_of_type}' does not exist in the registry. "
                f"Available types: {list(component_registry._registry.keys())}."
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

    # 3. select only the components related to "related_component"
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

    # 5. filter if "has_related_of_type" was specified.
    if has_related_of_type is not None:
        components_with_related_type = []
        for comp_name, component_dict in selected_components.items():
            related_components = component_registry.get_related_components(comp_name)
            if any(rel["type"] == has_related_of_type for rel in related_components):
                components_with_related_type.append(component_dict)
        selected_components = _intersect_component_lists(
            selected_components,
            components_with_related_type,
        )

    # Reconcile the download state of download required components against the
    # filesystem before returning. Downloads happen in the worker process, so
    # the in memory registry flag can be stale; a fresh check (a cheap folder
    # stat per downloadable component) keeps the list truthful.
    for comp_name, component_dict in selected_components.items():
        if getattr(component_dict.get("class"), "REQUIRES_DOWNLOAD", False):
            component_registry.refresh_download_status(comp_name)

    return [
        localize(_delete_class(component_dict), accept_language)
        for component_dict in selected_components.values()
    ]


@router.get("/{name}/download")
@inject
async def get_component_download_status(
    name: str,
    component_registry: "ComponentRegistry" = Depends(lambda: di["component_registry"]),
):
    """Return the reconciled download status of a component.

    Parameters
    ----------
    name : str
        The component class name.

    Returns
    -------
    dict
        ``{"downloaded": bool, "requires_download": bool}``.
    """
    try:
        component_class = component_registry[name]["class"]
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    requires = bool(getattr(component_class, "REQUIRES_DOWNLOAD", False))
    downloaded = component_registry.refresh_download_status(name)
    return {"downloaded": downloaded, "requires_download": requires}


@router.post("/{name}/download", status_code=status.HTTP_201_CREATED)
@inject
async def download_component(
    name: str,
    component_registry: "ComponentRegistry" = Depends(lambda: di["component_registry"]),
    job_queue=Depends(lambda: di["job_queue"]),
):
    """Enqueue a job to download the component's artifacts.

    Parameters
    ----------
    name : str
        The component class name.

    Returns
    -------
    dict
        ``{"id": job_id}`` of the enqueued download job.

    Raises
    ------
    HTTPException
        404 if unknown; 409 if not downloadable or already downloaded.
    """
    from DashAI.back.job.component_download_job import ComponentDownloadJob

    try:
        component_class = component_registry[name]["class"]
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    if not getattr(component_class, "REQUIRES_DOWNLOAD", False):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Component {name} does not require a download",
        )
    if component_registry.refresh_download_status(name):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Component {name} is already downloaded",
        )
    job = ComponentDownloadJob(component_name=name)
    job.set_status_as_delivered()
    job_id = job_queue.put(job).id
    return {"id": job_id}


@router.delete("/{name}/download", status_code=status.HTTP_204_NO_CONTENT)
@inject
async def delete_component_download(
    name: str,
    component_registry: "ComponentRegistry" = Depends(lambda: di["component_registry"]),
):
    """Delete a component's downloaded artifacts and reconcile its status.

    Parameters
    ----------
    name : str
        The component class name.
    """
    try:
        component_class = component_registry[name]["class"]
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    if not getattr(component_class, "REQUIRES_DOWNLOAD", False):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Component {name} does not support download and cannot be deleted",
        )
    component_class.delete()
    component_registry.refresh_download_status(name)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


class RequiredDownloadsParams(BaseModel):
    """Request body for resolving nested download-required components.

    Attributes
    ----------
    model_name : str or None
        The parent component being configured. When set and it still needs a
        download, it is included in the result so the caller can gate on a
        single list.
    parameters : dict
        The parameters dict as produced by the configuration UI.
    """

    model_name: Union[str, None] = None
    parameters: Dict[str, Any] = {}


@router.post("/downloads/required")
@inject
async def get_required_downloads(
    params: RequiredDownloadsParams,
    accept_language: str | None = Header(default=None),
    component_registry: "ComponentRegistry" = Depends(lambda: di["component_registry"]),
) -> List[Dict[str, Any]]:
    """Return the components a configuration still needs downloaded.

    Walks the ``parameters`` dict for nested components (a component selected as
    another component's parameter) and, optionally, checks the parent
    ``model_name`` itself. Each component is reconciled against the filesystem so
    the answer reflects downloads finished after startup.

    Parameters
    ----------
    params : RequiredDownloadsParams
        The parent ``model_name`` (optional) and its ``parameters`` dict.
    accept_language : str | None
        The 'Accept-Language' header used to localize display names.
    component_registry : ComponentRegistry
        Registry that resolves component classes and download state.

    Returns
    -------
    list[dict]
        One entry per not-yet-downloaded component, each with ``name``,
        ``display_name``, ``parent``, and ``download_size_bytes``.
    """
    from DashAI.back.dependencies.downloads.nested import missing_downloads

    missing = missing_downloads(params.parameters, component_registry)

    # Optionally fold in the parent model so callers can gate on one list.
    if params.model_name and params.model_name in component_registry:
        parent_class = component_registry[params.model_name]["class"]
        if getattr(
            parent_class, "REQUIRES_DOWNLOAD", False
        ) and not component_registry.refresh_download_status(params.model_name):
            missing.insert(
                0,
                {
                    "name": params.model_name,
                    "parent": None,
                    "download_size_bytes": getattr(
                        parent_class, "DOWNLOAD_SIZE_BYTES", None
                    ),
                },
            )

    def _localized_name(name: str) -> str:
        display = component_registry[name].get("display_name")
        if isinstance(display, MultilingualString):
            lang = (accept_language or "en").split("-")[0].lower()
            return display.get(lang)
        return display or name

    return [
        {**entry, "display_name": _localized_name(entry["name"])} for entry in missing
    ]


@router.get("/{id}/")
@inject
def get_component_by_id(
    id: str,
    accept_language: str | None = Header(default=None),
    component_registry: "ComponentRegistry" = Depends(lambda: di["component_registry"]),
) -> Dict[str, Any]:
    """Return a specific component using its id (the id is the component class name).

    Parameters
    ----------
    id : str
        A component identificator
    accept_language : str | None
        The 'Accept-Language' header from the request to localize multilingual
        strings in the component schema, by default None.
    component_registry: ComponentRegistry
        Registry that provides metadata and class references for the
        components available in DashAI.

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
            status_code=404,
            detail=f"Component {id} not found in the registry.",
        )
    raw = component_registry[id]
    return localize(_delete_class(raw), accept_language)


@router.post("/", status_code=status.HTTP_201_CREATED)
async def upload_component() -> None:
    """Create component placeholder.

    Raises
    ------
    HTTPException
        Always raises exception as it was intentionally not implemented.
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Method not implemented"
    )


@router.delete("/")
async def delete_component() -> None:
    """Delete component placeholder.

    Raises
    ------
    HTTPException
        Always raises exception as it was intentionally not implemented.
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Method not implemented"
    )


@router.patch("/")
async def update_component() -> None:
    """Update component placeholder.

    Raises
    ------
    HTTPException
        Always raises exception as it was intentionally not implemented.
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Method not implemented"
    )


@router.get("/{component_name}/children/")
async def get_child_components(
    component_name: str,
    recursive: bool = False,
    component_registry: "ComponentRegistry" = Depends(lambda: di["component_registry"]),
):
    """Get child components of a specific component.

    Args:
        component_name (str): The name of the component to get children for.
        recursive (bool): Whether to get child components recursively.

    Returns:
        List[Dict[str, Any]]: A list of child component dictionaries.
    """
    children_list = component_registry.get_child_components(
        component_name, recursive=recursive
    )
    return [_delete_class(child) for child in children_list]


@router.get("/image/{component_name}/", status_code=status.HTTP_200_OK)
async def get_component_image(
    component_name: str,
    component_registry: "ComponentRegistry" = Depends(lambda: di["component_registry"]),
    config: Dict[str, Any] = Depends(lambda: di["config"]),
) -> StreamingResponse:
    """Return the image of a specific component.

    Parameters
    ----------
    component_name : str
        The name of the component to retrieve the image for.
    component_registry: ComponentRegistry
        Registry that provides metadata and class references for the
        components available in DashAI.

    Returns
    -------
    StreamingResponse
        The image of the component.
    """
    import io

    import requests

    if component_name not in component_registry:
        raise HTTPException(
            status_code=404,
            detail=f"Component {component_name} not found in the registry.",
        )

    local_path_image = config["BACK_PATH"] / "static" / "images"
    image_path: str = (
        component_registry[component_name]
        .get("metadata", {})
        .get("image_preview", None)
    )
    cache_headers = {"Cache-Control": "public, max-age=3600"}

    if not image_path:
        with open(local_path_image / "placeholder.svg", "rb") as image_file:
            return StreamingResponse(
                io.BytesIO(image_file.read()),
                media_type="image/svg+xml",
                headers=cache_headers,
            )

    # If it is a URL, we obtain the image from the URL
    if image_path.startswith(("http://", "https://")):
        response = requests.get(image_path, timeout=5)
        if response.status_code == 200:
            return StreamingResponse(
                io.BytesIO(response.content),
                media_type="image/png",
                headers=cache_headers,
            )
        else:
            with open(local_path_image / "placeholder.svg", "rb") as image_file:
                return StreamingResponse(
                    io.BytesIO(image_file.read()),
                    media_type="image/svg+xml",
                    headers=cache_headers,
                )

    # Otherwise, we assume it is a local path
    try:
        with open(local_path_image / image_path, "rb") as image_file:
            return StreamingResponse(
                io.BytesIO(image_file.read()),
                media_type="image/png",
                headers=cache_headers,
            )
    except FileNotFoundError:
        with open(local_path_image / "placeholder.svg", "rb") as image_file:
            return StreamingResponse(
                io.BytesIO(image_file.read()),
                media_type="image/svg+xml",
                headers=cache_headers,
            )
