import logging
from typing import Callable, List, Optional

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, Query, Response, status
from fastapi.exceptions import HTTPException
from sqlalchemy import exc, select
from sqlalchemy.orm import Session
from typing_extensions import ContextManager

from DashAI.back.api.api_v1.schemas.plugin_params import (
    PluginParams,
    PluginUpdateParams,
)
from DashAI.back.containers import Container
from DashAI.back.dependencies.database.models import Plugin, Tag
from DashAI.back.dependencies.database.utils import add_plugin_to_db
from DashAI.back.dependencies.registry import ComponentRegistry
from DashAI.back.plugins.utils import (
    get_plugins_from_pypi,
    install_plugin_from_pypi,
    register_new_plugins,
)

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/")
@inject
async def get_plugins(
    session_factory: Callable[..., ContextManager[Session]] = Depends(
        Provide[Container.db.provided.session]
    ),
    tags: Optional[List[str]] = Query(None),
    plugin_status: Optional[str] = Query(None),
):
    """Retrieve a list of the stored plugins in the database.

    Parameters
    ----------
    tags: Optional[List[str]]
        List of tags used to retrieve only plugins with the desired tags.
    plugin_status: Optional[str]
        An string used to retrieve only plugins with the desired status.
    session_factory : Callable[..., ContextManager[Session]]
        A factory that creates a context manager that handles a SQLAlchemy session.
        The generated session can be used to access and query the database.

    Returns
    -------
    List[dict]
        A list of dictionaries representing the found plugins.
        Each dictionary contains information about the plugin, including its name,
        author, tags, description and creation date.
        If no plugins are found, an empty list will be returned.
    """
    with session_factory() as db:
        query = select(Plugin)
        if plugin_status:
            query = query.where(Plugin.status == plugin_status)
        if tags:
            query = query.join(Tag).where(Tag.name.in_(tags))
        try:
            plugins = db.scalars(query).unique().all()

        except exc.SQLAlchemyError as e:
            logger.exception(e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal database error",
            ) from e

    return plugins


@router.get("/{plugin_id}")
@inject
async def get_plugin(
    plugin_id: int,
    session_factory: Callable[..., ContextManager[Session]] = Depends(
        Provide[Container.db.provided.session]
    ),
):
    """Retrieve the plugin associated with the provided ID.

    Parameters
    ----------
    plugin_id : int
        ID of the plugin to retrieve.
    session_factory : Callable[..., ContextManager[Session]]
        A factory that creates a context manager that handles a SQLAlchemy session.
        The generated session can be used to access and query the database.

    Returns
    -------
    Dict
        A Dict containing the requested plugin details.
    """
    with session_factory() as db:
        try:
            plugin = db.get(Plugin, plugin_id)
            if not plugin:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Plugin not found",
                )

        except exc.SQLAlchemyError as e:
            logger.exception(e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal database error",
            ) from e

    return plugin


@router.post("/", status_code=status.HTTP_201_CREATED)
async def upload_plugin(params: List[PluginParams]):
    """Create a new batch of plugins in the DB.

    Parameters
    ----------
    params : List[PluginParams]
        The new plugins parameters.

    Returns
    -------
    List[Plugin]
        A list with the created plugins.
    """
    try:
        plugins = [add_plugin_to_db(param) for param in params]
        return plugins
    except exc.SQLAlchemyError as e:
        logger.exception(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal database error",
        ) from e


@router.post("/index", status_code=status.HTTP_201_CREATED)
async def refresh_plugins_record():
    """Request all DashAI plugins from index (for now PyPI) and add it to the DB.

    Parameters
    ----------

    Returns
    ----------
    List[Plugin]
        A list with the created plugins.
    """
    plugins_params = [
        PluginParams.model_validate(raw_plugin)
        for raw_plugin in get_plugins_from_pypi()
    ]
    try:
        plugins = [add_plugin_to_db(param) for param in plugins_params]
        return plugins
    except exc.SQLAlchemyError as e:
        logger.exception(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal database error",
        ) from e


@router.delete("/{plugin_id}")
@inject
async def delete_plugin(
    plugin_id: int,
    session_factory: Callable[..., ContextManager[Session]] = Depends(
        Provide[Container.db.provided.session]
    ),
):
    """Delete the plugin associated with the provided ID from the database.

    Parameters
    ----------
    plugin_id : int
        ID of the plugin to be deleted.
    session_factory : Callable[..., ContextManager[Session]]
        A factory that creates a context manager that handles a SQLAlchemy session.
        The generated session can be used to access and query the database.

    Returns
    -------
    Response with code 204 NO_CONTENT

    Raises
    ------
    HTTPException
        If the plugin with id plugin_id is not registered in the DB.
    """

    with session_factory() as db:
        try:
            plugin = db.get(Plugin, plugin_id)
            if not plugin:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Plugin not found",
                )
            db.delete(plugin)
            db.commit()
            return Response(status_code=status.HTTP_204_NO_CONTENT)
        except exc.SQLAlchemyError as e:
            logger.exception(e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal database error",
            ) from e


@router.patch("/{plugin_id}")
@inject
async def update_plugin(
    plugin_id: int,
    params: PluginUpdateParams,
    session_factory: Callable[..., ContextManager[Session]] = Depends(
        Provide[Container.db.provided.session]
    ),
    component_registry: ComponentRegistry = Depends(
        Provide[Container.component_registry]
    ),
):
    """Updates the status of a plugin with the provided ID.

    Parameters
    ----------
    plugin_id : int
        ID of the plugin to update.
    params : PluginUpdateParams
        The params to change in the plugin.
    session_factory : Callable[..., ContextManager[Session]]
        A factory that creates a context manager that handles a SQLAlchemy session.
        The generated session can be used to access and query the database.
    component_registry : ComponentRegistry
        The current app component registry provided by dependency injection.

    Returns
    -------
    Plugin
        The updated plugin.
    """
    with session_factory() as db:
        try:
            plugin = db.get(Plugin, plugin_id)
            plugin_name = plugin.name
            install_plugin_from_pypi(plugin_name)
            register_new_plugins(component_registry)
            if not plugin:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Plugin not found",
                )
            setattr(plugin, "status", params.new_status)
            db.commit()
            db.refresh(plugin)
            return plugin
        except exc.SQLAlchemyError as e:
            logger.exception(e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal database error",
            ) from e
