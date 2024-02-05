import logging
from typing import Callable

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, status
from fastapi.exceptions import HTTPException
from sqlalchemy import exc
from sqlalchemy.orm import Session
from typing_extensions import ContextManager

from DashAI.back.containers import Container
from DashAI.back.dependencies.database.models import Plugin
from DashAI.back.plugins.utils import get_plugins_from_pypi

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
router = APIRouter()


@router.get("/")
async def get_plugins():
    """Retrieve a list of the stored datasets in the database.

    Parameters
    ----------
    session_factory : Callable[..., ContextManager[Session]]
        A factory that creates a context manager that handles a SQLAlchemy session.
        The generated session can be used to access and query the database.

    Returns
    -------
    List[dict]
        A list of dictionaries representing the found datasets.
        Each dictionary contains information about the dataset, including its name,
        type, description, and creation date.
        If no datasets are found, an empty list will be returned.
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Method not implemented",
    )


@router.get("/{plugin_id}")
async def get_plugin(plugin_id: int):
    """Retrieve the dataset associated with the provided ID.

    Parameters
    ----------
    dataset_id : int
        ID of the dataset to retrieve.
    session_factory : Callable[..., ContextManager[Session]]
        A factory that creates a context manager that handles a SQLAlchemy session.
        The generated session can be used to access and query the database.

    Returns
    -------
    Dict
        A Dict containing the requested dataset details.
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Method not implemented",
    )


@inject
def add_plugin_to_db(
    raw_plugin: dict,
    session_factory: Callable[..., ContextManager[Session]] = Provide[
        Container.db.provided.session
    ],
) -> Plugin:
    with session_factory() as db:
        logging.debug("Storing plugin metadata in database.")
        try:
            plugin = Plugin(**raw_plugin)
            db.add(plugin)
            db.commit()
            db.refresh(plugin)

        except exc.SQLAlchemyError as e:
            logger.exception(e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal database error",
            ) from e
    return plugin


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
    plugins = get_plugins_from_pypi()
    map(add_plugin_to_db, plugins)
    return plugins


@router.delete("/{plugin_id}")
async def delete_plugin(plugin_id: int):
    """Delete the dataset associated with the provided ID from the database.

    Parameters
    ----------
    dataset_id : int
        ID of the dataset to be deleted.
    session_factory : Callable[..., ContextManager[Session]]
        A factory that creates a context manager that handles a SQLAlchemy session.
        The generated session can be used to access and query the database.

    Returns
    -------
    Response with code 204 NO_CONTENT
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Method not implemented",
    )


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
