import logging
import os
import uuid
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, NamedTuple

from fastapi import APIRouter, Depends, Query, Response, status
from fastapi.exceptions import HTTPException
from kink import di, inject
from sqlalchemy import exc

from DashAI.back.api.api_v1.schemas.notebook_params import Notebook as NotebookSchema
from DashAI.back.api.api_v1.schemas.notebook_params import (
    NotebookBulkDeleteParams,
    NotebookCreate,
    NotebookUpdateParams,
)
from DashAI.back.api.document_content import (
    image_response,
    read_content_page,
    read_outline,
    require_content_type,
)
from DashAI.back.core.enums.status import DocumentStatus
from DashAI.back.dependencies.database.models import (
    Converter,
    DataDocument,
    Dataset,
    Explorer,
    Notebook,
)

if TYPE_CHECKING:
    from sqlalchemy.orm import Session, sessionmaker

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)

router = APIRouter()

BASE_URL = "/api/v1/notebook"
DOCUMENT_NOTEBOOKS_DIR = "documents"


class _NotebookCopy(NamedTuple):
    """Where a new notebook copies its data from and to.

    Attributes
    ----------
    source : Path
        Directory copied into the notebook.
    destination : Path
        Directory that receives the copy.
    file_path : Path
        Working directory stored as ``Notebook.file_path``; deleting the
        notebook removes it.
    """

    source: Path
    destination: Path
    file_path: Path


def _plan_notebook_copy(
    db: "Session", params: NotebookCreate, config: Dict[str, Any]
) -> _NotebookCopy:
    """Resolve the notebook source and choose its working directory.

    Dataset notebooks copy the whole dataset directory under
    ``DATASETS_PATH``. Document notebooks copy only the parsed
    ``document/`` folder under ``NOTEBOOK_PATH/documents``, so the shared
    document is never written to.

    Parameters
    ----------
    db : Session
        Open database session.
    params : NotebookCreate
        Creation parameters with exactly one source.
    config : Dict[str, Any]
        Application config with ``DATASETS_PATH`` and ``NOTEBOOK_PATH``.

    Returns
    -------
    _NotebookCopy
        Source, destination and notebook working directory.

    Raises
    ------
    HTTPException
        404 when the source does not exist, 422 when the document has not
        finished parsing.
    """
    if params.document_id is not None:
        document = db.get(DataDocument, params.document_id)
        if document is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found",
            )
        if document.status != DocumentStatus.FINISHED or not document.file_path:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Document is not ready",
            )
        working_dir = (
            Path(config["NOTEBOOK_PATH"]) / DOCUMENT_NOTEBOOKS_DIR / uuid.uuid4().hex
        )
        return _NotebookCopy(
            source=Path(document.file_path) / "document",
            destination=working_dir / "document",
            file_path=working_dir,
        )

    dataset = db.get(Dataset, params.dataset_id)
    if dataset is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found",
        )
    working_dir = Path(config["DATASETS_PATH"]) / uuid.uuid4().hex[:8]
    return _NotebookCopy(
        source=Path(dataset.file_path),
        destination=working_dir,
        file_path=working_dir,
    )


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
        Name, description and exactly one of ``dataset_id`` or
        ``document_id``.
    session_factory : Callable[..., ContextManager[Session]]
        A factory that creates a context manager that handles a SQLAlchemy session.
        The generated session can be used to access and query the database.
    config : dict
        Application config with ``DATASETS_PATH`` and ``NOTEBOOK_PATH``.

    Returns
    -------
    schemas.Notebook
        The newly created notebook object.

    Raises
    ------
    HTTPException
        404 when the dataset or document does not exist, 422 when the
        document has not finished parsing, 500 when the copy or the database
        write fails.
    """
    import shutil

    db: "Session"

    with session_factory() as db:
        copy = _plan_notebook_copy(db, params, config)
        try:
            shutil.copytree(copy.source, copy.destination, dirs_exist_ok=True)
            notebook_model = Notebook(
                name=params.name or "Untitled Notebook",
                description=params.description,
                dataset_id=params.dataset_id,
                document_id=params.document_id,
                file_path=str(copy.file_path),
            )
            db.add(notebook_model)
            db.commit()
            db.refresh(notebook_model)

            return notebook_model
        except Exception as e:
            log.error(f"Error creating notebook: {e}")
            db.rollback()
            shutil.rmtree(copy.file_path, ignore_errors=True)
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


def _document_notebook_dir(session_factory: "sessionmaker", notebook_id: int) -> str:
    """Return the working copy directory of a document notebook.

    Parameters
    ----------
    session_factory : sessionmaker
        Session factory from the DI container.
    notebook_id : int
        ID of the notebook.

    Returns
    -------
    str
        ``<file_path>/document`` of the notebook.

    Raises
    ------
    HTTPException
        404 when the notebook does not exist, 422 when it is a dataset
        notebook.
    """
    with session_factory() as db:
        notebook = db.get(Notebook, notebook_id)
        if notebook is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notebook not found",
            )
        if notebook.data_kind != "document":
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Notebook is not a document notebook",
            )
        file_path = notebook.file_path
    return os.path.join(file_path, "document")


@router.get("/{notebook_id}/document-content")
@inject
def get_notebook_document_content(
    notebook_id: int,
    content_type: str = Query("all"),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    session_factory: "sessionmaker" = Depends(lambda: di["session_factory"]),
):
    """Return a page of the working copy items of a document notebook.

    Same item shape and paging as ``GET /documents/{id}/content``, read from
    the notebook's own copy; Image items point at the notebook image route.
    The handler is synchronous so FastAPI runs it in its threadpool.

    Parameters
    ----------
    notebook_id : int
        ID of the document notebook.
    content_type : str
        ``"all"``, ``"Text"`` or ``"Image"``.
    offset : int
        Index of the first item of the page.
    limit : int
        Page size, 1 to 500.
    session_factory : sessionmaker
        Session factory from the DI container.

    Returns
    -------
    dict
        ``notebook_id``, ``content_type``, ``total``, ``offset``, ``limit``
        and ``items``.

    Raises
    ------
    HTTPException
        404, 422 as in ``_document_notebook_dir``; 422 for an unknown type.
    """
    require_content_type(content_type)
    directory = _document_notebook_dir(session_factory, notebook_id)
    page = read_content_page(
        directory,
        content_type,
        offset,
        limit,
        lambda position: f"{BASE_URL}/{notebook_id}/document-images/{position}",
    )
    return {"notebook_id": notebook_id, **page}


@router.get("/{notebook_id}/document-outline")
@inject
def get_notebook_document_outline(
    notebook_id: int,
    session_factory: "sessionmaker" = Depends(lambda: di["session_factory"]),
):
    """Return the structure of a document notebook's working copy.

    Parameters
    ----------
    notebook_id : int
        ID of the document notebook.
    session_factory : sessionmaker
        Session factory from the DI container.

    Returns
    -------
    dict
        ``notebook_id``, ``total`` and ``items``; each item has
        ``position``, ``type``, ``kind``, ``page``, ``level`` and ``label``.

    Raises
    ------
    HTTPException
        404, 422 as in ``_document_notebook_dir``.
    """
    outline = read_outline(_document_notebook_dir(session_factory, notebook_id))
    return {"notebook_id": notebook_id, **outline}


@router.get("/{notebook_id}/document-images/{position}")
@inject
def get_notebook_document_image(
    notebook_id: int,
    position: int,
    session_factory: "sessionmaker" = Depends(lambda: di["session_factory"]),
):
    """Serve one Image item of a document notebook's working copy.

    The response is marked ``no-cache``: notebook ids are reused once a row
    is deleted, and the working copy is what notebook tools rewrite.

    Parameters
    ----------
    notebook_id : int
        ID of the document notebook.
    position : int
        Global position of the item.
    session_factory : sessionmaker
        Session factory from the DI container.

    Returns
    -------
    Response
        The image bytes.

    Raises
    ------
    HTTPException
        404 when the position is not an image; 404, 422 as in
        ``_document_notebook_dir``.
    """
    return image_response(
        _document_notebook_dir(session_factory, notebook_id),
        position,
        headers={"Cache-Control": "no-cache"},
    )


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
