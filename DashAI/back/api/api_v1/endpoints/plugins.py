import logging

from fastapi import APIRouter, status
from fastapi.exceptions import HTTPException

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


@router.post("/")
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
