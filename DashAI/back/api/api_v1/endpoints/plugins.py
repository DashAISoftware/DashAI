import logging
from typing import Callable

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, Response, status
from fastapi.exceptions import HTTPException
from sqlalchemy import exc
from sqlalchemy.orm import Session
from typing_extensions import ContextManager

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
    raw_plugin: dict,
    session_factory: Callable[..., ContextManager[Session]] = Provide[
        Container.db.provided.session
    ],
) -> Plugin:
    with session_factory() as db:
        logging.debug("Storing plugin metadata in database.")
        raw_tags = raw_plugin.pop("keywords")
        try:
            plugin = Plugin(**raw_plugin)
            db.add(plugin)
            db.commit()
            db.refresh(plugin)

            for raw_tag in raw_tags:
                tag = Tag(
                    plugin_id=plugin.id,
                    name=raw_tag,
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
async def upload_plugin():
    """Create a new dataset from a file or url.

    Parameters
    ----------
    params : str, optional
        A Dict containing configuration options for the new dataset.
    url : str, optional
        URL of the dataset file, mutually exclusive with uploading a file, by default
        Form(None).
    file : UploadFile, optional
        File object containing the dataset data, mutually exclusive with
        providing a URL, by default File(None).
    component_registry : ComponentRegistry
        Registry containing the current app available components.
    session_factory : Callable[..., ContextManager[Session]]
        A factory that creates a context manager that handles a SQLAlchemy session.
        The generated session can be used to access and query the database.
    config: Dict[str, Any]
        Application settings.

    Returns
    -------
    Dataset
        The created dataset.
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Method not implemented",
    )


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
    raw_plugins = get_plugins_from_pypi()
    plugins = [add_plugin_to_db(raw_plugin) for raw_plugin in raw_plugins]
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
async def update_plugin(plugin_id: int):
    """Updates the name and/or task name of a dataset with the provided ID.

    Parameters
    ----------
    dataset_id : int
        ID of the dataset to update.
    name : str, optional
        New name for the dataset.
    task_name : str, optional
        New task name for the dataset.
    session_factory : Callable[..., ContextManager[Session]]
        A factory that creates a context manager that handles a SQLAlchemy session.
        The generated session can be used to access and query the database.

    Returns
    -------
    Dict
        A dictionary containing the updated dataset record.
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Method not implemented",
    )
