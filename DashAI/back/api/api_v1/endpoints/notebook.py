import logging
from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends, Response, status
from fastapi.exceptions import HTTPException
from kink import di, inject
from sqlalchemy import exc

from DashAI.back.api.api_v1.schemas.notebook_params import Notebook as NotebookSchema
from DashAI.back.api.api_v1.schemas.notebook_params import (
    NotebookBulkDeleteParams,
    NotebookCreate,
    NotebookUpdateParams,
)
from DashAI.back.dependencies.database.models import (
    Converter,
    Dataset,
    Explorer,
    Notebook,
)

if TYPE_CHECKING:
    from sqlalchemy.orm import Session, sessionmaker

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)

router = APIRouter()


@router.post("/", response_model=NotebookSchema, status_code=status.HTTP_201_CREATED)
@inject
def create_notebook(
    params: NotebookCreate,
    session_factory: "sessionmaker" = Depends(lambda: di["session_factory"]),
    config: dict = Depends(lambda: di["config"]),
):
    """Create a new notebook entry in the database.

    Parameters
    ----------
    params : schemas.NotebookCreate
        The parameters for creating a notebook.
    session_factory : Callable[..., ContextManager[Session]]
        A factory that creates a context manager that handles a SQLAlchemy session.
        The generated session can be used to access and query the database.

    Returns
    -------
    schemas.Notebook
        The newly created notebook object.

    Raises
    ------
    HTTPException
        If there is an error creating the notebook, returns a 500 Internal Server Error.
    """
    import os
    import shutil
    import uuid

    db: "Session"

    with session_factory() as db:
        try:
            dataset_id = params.dataset_id
            # Get the dataset
            dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()

            # Copy the dataset
            dataset_folder = dataset.file_path
            random_name = uuid.uuid4().hex[:8]
            new_folder_path = os.path.join(
                config["DATASETS_PATH"],
                random_name,
            )
            os.makedirs(new_folder_path, exist_ok=True)
            shutil.copytree(dataset_folder, new_folder_path, dirs_exist_ok=True)

            notebook_data = params.model_dump()
            notebook_data = {
                **notebook_data,
                "name": notebook_data.get("name") or "Untitled Notebook",
            }
            notebook_data["file_path"] = new_folder_path
            notebook_model = Notebook(**notebook_data)
            db.add(notebook_model)
            db.commit()
            db.refresh(notebook_model)

            return notebook_model
        except Exception as e:
            log.error(f"Error creating notebook: {e}")
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create notebook",
            ) from e


@router.get("/", response_model=list[NotebookSchema])
@inject
def get_notebooks(
    session_factory: "sessionmaker" = Depends(lambda: di["session_factory"]),
):
    """Get all notebooks from the database.

    Parameters
    ----------
    session_factory : Callable[..., ContextManager[Session]]
        A factory that creates a context manager that handles a SQLAlchemy session.

    Returns
    -------
    list[schemas.Notebook]
        A list of all notebooks in the database.

    Raises
    ------
    HTTPException
        If there is an error retrieving notebooks, returns a 500 Internal Server Error.
    """
    db: Session
    with session_factory() as db:
        try:
            notebooks = db.query(Notebook).all()

        except Exception as e:
            log.error(f"Error retrieving notebooks: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve notebooks",
            ) from e

    return notebooks


@router.get("/{notebook_id}", response_model=NotebookSchema)
@inject
def get_notebook(
    notebook_id: int,
    session_factory: "sessionmaker" = Depends(lambda: di["session_factory"]),
):
    """Get a notebook by its ID.

    Parameters
    ----------
    notebook_id : int
        ID of the notebook to retrieve.
    session_factory : Callable[..., ContextManager[Session]]
        A factory that creates a context manager that handles a SQLAlchemy session.
        The generated session can be used to access and query the database.

    Returns
    -------
    schemas.Notebook
        The notebook object with the specified ID.

    Raises
    ------
    HTTPException
        If the notebook is not found, returns a 404 Not Found error.
    """
    db: Session
    with session_factory() as db:
        notebook = db.query(Notebook).filter(Notebook.id == notebook_id).first()
        if not notebook:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notebook not found",
            ) from None

        return notebook


@router.get("/{notebook_id}/explorers")
@inject
def get_notebook_explorer_list(
    notebook_id: int,
    skip: int = 0,
    limit: int = 0,
    session_factory: "sessionmaker" = Depends(lambda: di["session_factory"]),
):
    """Get all explorers associated with a notebook.

    Parameters
    ----------
    notebook_id : int
        ID of the notebook.
    session_factory : Callable[..., ContextManager[Session]]
        A factory that creates a context manager that handles a SQLAlchemy session.
        The generated session can be used to access and query the database.

    Returns
    -------
    explorers : List[explorer_schemas.Explorer]
        List of explorers associated with the notebook.

    Raises
    ------
    HTTPException
        If there is an error retrieving explorers, returns a 500 Internal Server Error.
    """
    db: Session
    with session_factory() as db:
        explorers = db.query(Explorer).filter(Explorer.notebook_id == notebook_id)

        if skip > 0:
            explorers = explorers.offset(skip)
        if limit > 0:
            explorers = explorers.limit(limit)

        return explorers.all()


@router.get("/{notebook_id}/converters")
@inject
async def get_notebook_converter(
    notebook_id: int,
    session_factory: "sessionmaker" = Depends(lambda: di["session_factory"]),
):
    """Get all converters associated with a notebook.

    Parameters
    ----------
    notebook_id : int
        ID of the notebook.
    session_factory : Callable[..., ContextManager[Session]]
        Dependency-injected SQLAlchemy session factory.

    Returns
    -------
    Converter
        The converter list associated with the notebook.

    Raises
    ------
        HTTPException: If there is an error retrieving the converter list,
        returns a 500 Internal Server Error.
    """
    with session_factory() as db:
        try:
            converter = (
                db.query(Converter).filter(Converter.notebook_id == notebook_id).all()
            )

            return converter
        except Exception as e:
            log.error(
                f"Error retrieving converter list for notebook {notebook_id}: {e}"
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to retrieve converter from notebook {notebook_id}",
            ) from e


@router.delete("/")
@inject
async def delete_notebooks(
    params: NotebookBulkDeleteParams,
    session_factory: "sessionmaker" = Depends(lambda: di["session_factory"]),
):
    """Delete multiple notebooks, in a single transaction.

    Parameters
    ----------
    params : NotebookBulkDeleteParams
        The IDs of the notebooks to delete. IDs that do not match an existing
        notebook are silently skipped rather than failing the whole request.
    session_factory : Callable[..., ContextManager[Session]]
        A factory that creates a context manager that handles a SQLAlchemy session.
        The generated session can be used to access and query the database.

    Returns
    -------
    Response with code 204 NO_CONTENT
    """
    import shutil

    log.debug("Deleting notebooks with ids %s", params.ids)
    file_paths = []
    with session_factory() as db:
        try:
            for notebook_id in params.ids:
                notebook = db.get(Notebook, notebook_id)
                if not notebook:
                    continue
                file_paths.append(notebook.file_path)
                db.delete(notebook)

            db.commit()

        except exc.SQLAlchemyError as e:
            log.exception(e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal database error",
            ) from e

    for file_path in file_paths:
        shutil.rmtree(file_path, ignore_errors=True)

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete("/{notebook_id}")
@inject
async def delete_notebook(
    notebook_id: int,
    session_factory: "sessionmaker" = Depends(lambda: di["session_factory"]),
):
    """Delete the notebook associated with the provided ID from the database.

    Parameters
    ----------
    notebook_id : int
        ID of the notebook to be deleted.
    session_factory : Callable[..., ContextManager[Session]]
        A factory that creates a context manager that handles a SQLAlchemy session.
        The generated session can be used to access and query the database.

    Returns
    -------
    Response with code 204 NO_CONTENT

    Raises
    ------
    HTTPException
        If the notebook is not registered in the DB.
    """
    log.debug("Deleting notebook with id %s", notebook_id)
    import shutil

    with session_factory() as db:
        try:
            notebook = db.get(Notebook, notebook_id)
            if not notebook:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Notebook not found",
                )

            shutil.rmtree(notebook.file_path, ignore_errors=True)

            db.delete(notebook)
            db.commit()

        except exc.SQLAlchemyError as e:
            log.exception(e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal database error",
            ) from e

    try:
        shutil.rmtree(notebook.file_path, ignore_errors=True)
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    except OSError as e:
        log.exception(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete directory",
        ) from e


@router.patch("/{notebook_id}")
@inject
async def update_notebook(
    notebook_id: int,
    params: NotebookUpdateParams,
    session_factory: "sessionmaker" = Depends(lambda: di["session_factory"]),
):
    """Updates the name of a notebook with the provided ID.

    Parameters
    ----------
    notebook_id : int
        ID of the notebook to update.
    params : NotebookUpdateParams
        A dictionary containing the new values for the notebook.
        name : str
            New name for the notebook.
    session_factory : Callable[..., ContextManager[Session]]
        A factory that creates a context manager that handles a SQLAlchemy session.
        The generated session can be used to access and query the database.

    Returns
    -------
    Dict
        A dictionary containing the updated dataset record.
    """
    with session_factory() as db:
        notebook = db.get(Notebook, notebook_id)
        if not notebook:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notebook not found",
            )

        if not params.name or not params.name.strip():
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Name cannot be empty",
            )

        new_name = params.name.strip()

        if new_name == notebook.name:
            return notebook

        notebook.name = new_name
        try:
            db.commit()
            db.refresh(notebook)
        except exc.SQLAlchemyError as e:
            db.rollback()
            log.error(f"Database error updating notebook {notebook_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal database error",
            ) from e

    return notebook
