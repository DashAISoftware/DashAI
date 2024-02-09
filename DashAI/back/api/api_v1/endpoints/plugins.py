import logging
from typing import Callable, List

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, Response, status
from fastapi.exceptions import HTTPException
from sqlalchemy import exc
from sqlalchemy.orm import Session
from typing_extensions import ContextManager

from DashAI.back.api.api_v1.schemas.plugin_params import (
    PluginParams,
    PluginUpdateParams,
)
from DashAI.back.containers import Container
from DashAI.back.dependencies.database.models import Plugin, Tag
from DashAI.back.plugins.utils import get_plugins_from_pypi

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
router = APIRouter()


@router.get("/")
@inject
async def get_plugins(
    session_factory: Callable[..., ContextManager[Session]] = Provide[
        Container.db.provided.session
    ],
):
    """Retrieve a list of the stored plugins in the database.

    Parameters
    ----------
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
        try:
            plugins = db.query(Plugin).all()

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
    session_factory: Callable[..., ContextManager[Session]] = Provide[
        Container.db.provided.session
    ],
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


@inject
def add_plugin_to_db(
    raw_plugin: PluginParams,
    session_factory: Callable[..., ContextManager[Session]] = Provide[
        Container.db.provided.session
    ],
) -> Plugin:
    """Create a Plugin from a PluginParams instance and store it in the DB.

    Parameters
    ----------
    params : List[PluginParams]
        The new plugins parameters.

    Returns
    -------
    List[Plugin]
        A list with the created plugins.
    """
    with session_factory() as db:
        logging.debug("Storing plugin metadata in database.")
        raw_tags = raw_plugin.tags
        try:
            plugin = Plugin(
                name=raw_plugin.name,
                author=raw_plugin.author,
                summary=raw_plugin.summary,
                description=raw_plugin.description,
                description_content_type=raw_plugin.description_content_type,
            )
            db.add(plugin)
            db.commit()
            db.refresh(plugin)

            for raw_tag in raw_tags:
                tag = Tag(
                    plugin_id=plugin.id,
                    name=raw_tag.name,
                )
                db.add(tag)
                db.commit()
            db.refresh(plugin)

            return plugin

        except exc.SQLAlchemyError as e:
            logger.exception(e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal database error",
            ) from e


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
    plugins = [add_plugin_to_db(param) for param in params]
    return plugins


@router.post("/refresh", status_code=status.HTTP_201_CREATED)
async def refresh_plugins_record():
    """Request all DashAI plugins from PyPI and add it to the DB.

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
    plugins = [add_plugin_to_db(param) for param in plugins_params]
    return plugins


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

    Returns
    -------
    Plugin
        The updated plugin.
    """
    with session_factory() as db:
        try:
            plugin = db.get(Plugin, plugin_id)
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
