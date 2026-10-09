"""Endpoints for the persistent documents of the Data module.

Mounted at ``/api/v1/documents``. The session scoped RAG documents keep their
own router at ``/api/v1/document`` until branch 5 retires it.
"""

import json
import logging
import os
import shutil
import uuid
from pathlib import Path
from typing import TYPE_CHECKING, List

from fastapi import APIRouter, Depends, Query, Response, status
from fastapi.exceptions import HTTPException
from fastapi.responses import FileResponse
from kink import di, inject
from pydantic import ValidationError
from sqlalchemy import exc, select

from DashAI.back.api.api_v1.schemas.data_documents_params import (
    DataDocumentCreateParams,
    DataDocumentFromNotebookParams,
    DataDocumentSchema,
    DataDocumentUpdateParams,
)
from DashAI.back.api.document_content import (
    image_response,
    read_content_page,
    read_outline,
    require_content_type,
)
from DashAI.back.core.enums.status import ConverterStatus, DocumentStatus
from DashAI.back.dataloaders.classes.dataloader import (
    DataKindMismatchError,
    require_data_kind,
)
from DashAI.back.dependencies.database.models import (
    Converter,
    DataDocument,
    Folder,
    Notebook,
)
from DashAI.back.services.RAG.deferred_fs import remove_after_commit

if TYPE_CHECKING:
    from sqlalchemy.orm import Session, sessionmaker

    from DashAI.back.dependencies.registry import ComponentRegistry

logger = logging.getLogger(__name__)

router = APIRouter()

BASE_URL = "/api/v1/documents"
BUSY_STATUSES = (DocumentStatus.DELIVERED, DocumentStatus.STARTED)


def _document_loader_class(component_registry: "ComponentRegistry", name: str) -> type:
    """Resolve a document loader class by name.

    Parameters
    ----------
    component_registry : ComponentRegistry
        The registry from the DI container.
    name : str
        Loader component name.

    Returns
    -------
    type
        The loader class.

    Raises
    ------
    HTTPException
        422 if the name is unknown or the loader does not produce documents.
    """
    if name not in component_registry:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Document loader '{name}' does not exist.",
        )
    loader_class = component_registry[name]["class"]
    try:
        require_data_kind(loader_class, "document")
    except DataKindMismatchError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)
        ) from e
    return loader_class


def _get_document_or_404(db: "Session", document_id: int) -> DataDocument:
    """Fetch a document row or fail with 404.

    Parameters
    ----------
    db : Session
        An open session.
    document_id : int
        Primary key.

    Returns
    -------
    DataDocument
        The row.

    Raises
    ------
    HTTPException
        404 if there is no such row.
    """
    document = db.get(DataDocument, document_id)
    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Document not found"
        )
    return document


@router.post(
    "/", response_model=DataDocumentSchema, status_code=status.HTTP_201_CREATED
)
@inject
async def create_data_document(
    params: DataDocumentCreateParams,
    session_factory: "sessionmaker" = Depends(lambda: di["session_factory"]),
    component_registry: "ComponentRegistry" = Depends(lambda: di["component_registry"]),
):
    """Create a NOT_STARTED document row before its upload job runs.

    Parameters
    ----------
    params : DataDocumentCreateParams
        Name, file name, loader and loader parameters.
    session_factory : sessionmaker
        Session factory from the DI container.
    component_registry : ComponentRegistry
        Registry from the DI container.

    Returns
    -------
    DataDocument
        The placeholder row, with the loader parameters resolved.

    Raises
    ------
    HTTPException
        409 for a taken name; 422 for an empty name, a wrong loader, an
        unsupported extension or invalid parameters; 500 on database errors.
    """
    name = params.name.strip()
    if not name:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Name cannot be empty",
        )
    file_name = os.path.basename(params.file_name)
    loader_class = _document_loader_class(component_registry, params.dataloader)
    if not loader_class.supports_file(file_name):
        accepted = ", ".join(sorted(loader_class.SUPPORTED_EXTENSIONS))
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"{params.dataloader} accepts {accepted} files, not '{file_name}'.",
        )
    try:
        resolved_params = loader_class().resolve_params(params.dataloader_params)
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)
        ) from e

    with session_factory() as db:
        taken = db.execute(
            select(DataDocument.id).where(DataDocument.name == name)
        ).scalar()
        if taken:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"A document with the name '{name}' already exists",
            )
        document = DataDocument(
            name=name,
            file_name=file_name,
            file_type=Path(file_name).suffix.lower().lstrip("."),
            file_hash="",
            file_path="",
            dataloader=params.dataloader,
            dataloader_params=resolved_params,
            content_counts={},
            status=DocumentStatus.NOT_STARTED,
        )
        db.add(document)
        try:
            db.commit()
        except exc.IntegrityError as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"A document with the name '{name}' already exists",
            ) from e
        except exc.SQLAlchemyError as e:
            db.rollback()
            logger.exception(e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal database error",
            ) from e
        db.refresh(document)
        return document


def _copy_notebook_document(
    working_copy: str, target: Path, derived_from: dict
) -> dict:
    """Copy a notebook's working copy into a new document folder.

    Parameters
    ----------
    working_copy : str
        The notebook's ``document`` directory.
    target : Path
        The new ``<DOCUMENTS_PATH>/<uuid>`` folder; must not exist.
    derived_from : dict
        Where the document comes from, stored in its metadata.

    Returns
    -------
    dict
        The item counts of the copied document, keyed by type name.
    """
    shutil.copytree(working_copy, target / "document")
    sidecar_path = target / "document" / "document.json"
    with open(sidecar_path, "r", encoding="utf-8") as f:
        sidecar = json.load(f)
    sidecar["metadata"] = {**sidecar.get("metadata", {}), "derived_from": derived_from}
    with open(sidecar_path, "w", encoding="utf-8") as f:
        json.dump(sidecar, f, indent=2, sort_keys=True, ensure_ascii=False)
    return sidecar.get("content_counts", {})


@router.post(
    "/from-notebook",
    response_model=DataDocumentSchema,
    status_code=status.HTTP_201_CREATED,
)
@inject
def create_data_document_from_notebook(
    params: DataDocumentFromNotebookParams,
    session_factory: "sessionmaker" = Depends(lambda: di["session_factory"]),
    config=Depends(lambda: di["config"]),
):
    """Save the working copy of a document notebook as a new document.

    The new document keeps the file name, loader and page count of the
    document the notebook was created from, has no source file, and records
    its origin in its metadata. The handler is synchronous so FastAPI runs
    the copy in its threadpool.

    Parameters
    ----------
    params : DataDocumentFromNotebookParams
        Name of the new document and the notebook to save.
    session_factory : sessionmaker
        Session factory from the DI container.
    config : dict
        App configuration with ``DOCUMENTS_PATH``.

    Returns
    -------
    DataDocument
        The new, finished document.

    Raises
    ------
    HTTPException
        404 for an unknown notebook; 409 for a taken name or while a
        converter of the notebook is still running; 422 for an empty name or
        a dataset notebook; 500 when the copy or the database fails.
    """
    from DashAI.back.dataloaders.classes.notebook_data import notebook_data_path

    name = params.name.strip()
    if not name:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Name cannot be empty",
        )
    with session_factory() as db:
        notebook = db.get(Notebook, params.notebook_id)
        if notebook is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Notebook not found"
            )
        if notebook.data_kind != "document":
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Only document notebooks can be saved as documents",
            )
        running = db.execute(
            select(Converter.id).where(
                Converter.notebook_id == notebook.id,
                Converter.status.notin_(
                    [ConverterStatus.FINISHED, ConverterStatus.ERROR]
                ),
            )
        ).first()
        if running:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Wait for the notebook converters to finish",
            )
        taken = db.execute(
            select(DataDocument.id).where(DataDocument.name == name)
        ).scalar()
        if taken:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"A document with the name '{name}' already exists",
            )

        source = notebook.document
        target = Path(config["DOCUMENTS_PATH"]) / uuid.uuid4().hex
        try:
            counts = _copy_notebook_document(
                notebook_data_path(notebook),
                target,
                {
                    "document_id": source.id,
                    "document_name": source.name,
                    "notebook_id": notebook.id,
                    "notebook_name": notebook.name,
                },
            )
        except (OSError, ValueError) as e:
            shutil.rmtree(target, ignore_errors=True)
            logger.exception(e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="The notebook document could not be copied",
            ) from e

        document = DataDocument(
            name=name,
            file_name=source.file_name,
            file_type=source.file_type,
            file_hash="",
            file_path=os.path.realpath(target),
            dataloader=source.dataloader,
            dataloader_params=source.dataloader_params,
            content_counts=counts,
            total_pages=source.total_pages,
            status=DocumentStatus.FINISHED,
        )
        db.add(document)
        try:
            db.commit()
        except exc.SQLAlchemyError as e:
            db.rollback()
            shutil.rmtree(target, ignore_errors=True)
            if isinstance(e, exc.IntegrityError):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"A document with the name '{name}' already exists",
                ) from e
            logger.exception(e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal database error",
            ) from e
        db.refresh(document)
        return document


@router.get("/", response_model=List[DataDocumentSchema])
@inject
async def get_data_documents(
    session_factory: "sessionmaker" = Depends(lambda: di["session_factory"]),
):
    """List every document.

    Parameters
    ----------
    session_factory : sessionmaker
        Session factory from the DI container.

    Returns
    -------
    List[DataDocument]
        All rows ordered by id.

    Raises
    ------
    HTTPException
        500 on database errors.
    """
    with session_factory() as db:
        try:
            return db.query(DataDocument).order_by(DataDocument.id).all()
        except exc.SQLAlchemyError as e:
            logger.exception(e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal database error",
            ) from e


@router.get("/{document_id}", response_model=DataDocumentSchema)
@inject
async def get_data_document(
    document_id: int,
    session_factory: "sessionmaker" = Depends(lambda: di["session_factory"]),
):
    """Get one document.

    Parameters
    ----------
    document_id : int
        Primary key.
    session_factory : sessionmaker
        Session factory from the DI container.

    Returns
    -------
    DataDocument
        The row.

    Raises
    ------
    HTTPException
        404 if there is no such document.
    """
    with session_factory() as db:
        return _get_document_or_404(db, document_id)


@router.patch("/{document_id}", response_model=DataDocumentSchema)
@inject
async def update_data_document(
    document_id: int,
    params: DataDocumentUpdateParams,
    session_factory: "sessionmaker" = Depends(lambda: di["session_factory"]),
):
    """Rename a document and/or move it to a folder.

    Parameters
    ----------
    document_id : int
        Primary key.
    params : DataDocumentUpdateParams
        New name and/or folder.
    session_factory : sessionmaker
        Session factory from the DI container.

    Returns
    -------
    DataDocument
        The updated row.

    Raises
    ------
    HTTPException
        404 for an unknown document or folder, 409 for a taken name, 422 for
        an empty name, 500 on database errors.
    """
    with session_factory() as db:
        document = _get_document_or_404(db, document_id)

        if params.name is not None:
            new_name = params.name.strip()
            if not new_name:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Name cannot be empty",
                )
            if new_name != document.name:
                taken = db.execute(
                    select(DataDocument.id).where(
                        DataDocument.name == new_name, DataDocument.id != document_id
                    )
                ).scalar()
                if taken:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail="Document name already exists",
                    )
                document.name = new_name

        if "folder_id" in params.model_fields_set:
            if (
                params.folder_id is not None
                and db.get(Folder, params.folder_id) is None
            ):
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="Folder not found"
                )
            document.folder_id = params.folder_id

        try:
            db.commit()
        except exc.IntegrityError as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Document name already exists",
            ) from e
        except exc.SQLAlchemyError as e:
            db.rollback()
            logger.exception(e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal database error",
            ) from e
        db.refresh(document)
        return document


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
@inject
async def delete_data_document(
    document_id: int,
    session_factory: "sessionmaker" = Depends(lambda: di["session_factory"]),
):
    """Delete a document row, its notebooks and, once that commits, their folders.

    The notebooks go through the ORM cascade on DataDocument.notebooks,
    because SQLite does not enforce the foreign key cascade.

    A document whose job is queued or running cannot be deleted: the job
    would recreate the folder after the row is gone. Cancelling the job moves
    it to ERROR, after which deleting works.

    Parameters
    ----------
    document_id : int
        Primary key.
    session_factory : sessionmaker
        Session factory from the DI container.

    Returns
    -------
    Response
        204 No Content.

    Raises
    ------
    HTTPException
        404 for an unknown document, 409 while it is being parsed, 500 on
        database errors.
    """
    with session_factory() as db:
        document = _get_document_or_404(db, document_id)
        if document.status in BUSY_STATUSES:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "The document is still being parsed. "
                    "Cancel its job before deleting it."
                ),
            )
        remove_after_commit(db, document.file_path)
        for notebook in document.notebooks:
            remove_after_commit(db, notebook.file_path)
        db.delete(document)
        try:
            db.commit()
        except exc.SQLAlchemyError as e:
            db.rollback()
            logger.exception(e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal database error",
            ) from e
    return Response(status_code=status.HTTP_204_NO_CONTENT)


def _document_dir(session_factory: "sessionmaker", document_id: int) -> str:
    """Return the parsed content directory of a FINISHED row.

    Parameters
    ----------
    session_factory : sessionmaker
        Session factory from the DI container.
    document_id : int
        Primary key.

    Returns
    -------
    str
        ``<file_path>/document``.

    Raises
    ------
    HTTPException
        404 for an unknown document, 409 while it has not finished parsing.
    """
    with session_factory() as db:
        document = _get_document_or_404(db, document_id)
        _require_finished(document)
        file_path = document.file_path
    return os.path.join(file_path, "document")


def _require_finished(document: DataDocument) -> None:
    """Fail with 409 unless the document finished parsing.

    Parameters
    ----------
    document : DataDocument
        The row to check.

    Raises
    ------
    HTTPException
        409 when the status is not FINISHED or the row has no folder.
    """
    if document.status != DocumentStatus.FINISHED or not document.file_path:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="The document has not finished parsing.",
        )


@router.get("/{document_id}/content")
@inject
def get_data_document_content(
    document_id: int,
    content_type: str = Query("all"),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    session_factory: "sessionmaker" = Depends(lambda: di["session_factory"]),
):
    """Return a page of the document items, in reading order.

    Only the requested content types are read, and image bytes never are:
    an Image item carries the URL that serves it. The handler is synchronous
    so FastAPI runs it in its threadpool instead of the event loop.

    Parameters
    ----------
    document_id : int
        Primary key.
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
        ``document_id``, ``content_type``, ``total``, ``offset``, ``limit``
        and ``items``.

    Raises
    ------
    HTTPException
        404, 409 as in ``_document_dir``; 422 for an unknown type.
    """
    require_content_type(content_type)
    directory = _document_dir(session_factory, document_id)
    page = read_content_page(
        directory,
        content_type,
        offset,
        limit,
        lambda position: f"{BASE_URL}/{document_id}/images/{position}",
    )
    return {"document_id": document_id, **page}


@router.get("/{document_id}/outline")
@inject
def get_data_document_outline(
    document_id: int,
    session_factory: "sessionmaker" = Depends(lambda: di["session_factory"]),
):
    """Return the structure of the whole document without its content.

    Every item comes back in reading order with its type, kind and page,
    plus a short single line label for titles, headings and captions, so a
    client can draw an outline or a reading order map without loading the
    document.

    Parameters
    ----------
    document_id : int
        Primary key.
    session_factory : sessionmaker
        Session factory from the DI container.

    Returns
    -------
    dict
        ``document_id``, ``total`` and ``items``; each item has
        ``position``, ``type``, ``kind``, ``page``, ``level`` and ``label``.

    Raises
    ------
    HTTPException
        404, 409 as in ``_document_dir``.
    """
    outline = read_outline(_document_dir(session_factory, document_id))
    return {"document_id": document_id, **outline}


@router.get("/{document_id}/images/{position}")
@inject
def get_data_document_image(
    document_id: int,
    position: int,
    session_factory: "sessionmaker" = Depends(lambda: di["session_factory"]),
):
    """Serve one Image item by its reading order position.

    Only that item's bytes are copied out of the image file.

    Parameters
    ----------
    document_id : int
        Primary key.
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
        404 when the position is not an image; 404, 409 as in
        ``_document_dir``.
    """
    return image_response(_document_dir(session_factory, document_id), position)


def _serve_source(
    document_id: int, disposition: str, session_factory: "sessionmaker"
) -> FileResponse:
    """Serve the original uploaded file.

    Parameters
    ----------
    document_id : int
        Primary key.
    disposition : str
        ``"inline"`` or ``"attachment"``.
    session_factory : sessionmaker
        Session factory from the DI container.

    Returns
    -------
    FileResponse
        The file under ``<file_path>/source/<file_name>``, marked ``no-cache``
        so a browser revalidates it. Ids are reused once a row is deleted, and
        without this a cached file from the previous owner of the id is served.

    Raises
    ------
    HTTPException
        404 for an unknown document or a missing file, 409 while parsing.
    """
    with session_factory() as db:
        document = _get_document_or_404(db, document_id)
        _require_finished(document)
        file_name = document.file_name
        file_type = document.file_type
        path = Path(document.file_path) / "source" / (file_name or "")
    if not file_name or not path.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Source file not found"
        )
    media_type = (
        "application/pdf" if file_type == "pdf" else "text/plain; charset=utf-8"
    )
    return FileResponse(
        path,
        media_type=media_type,
        filename=file_name,
        content_disposition_type=disposition,
        headers={"Cache-Control": "no-cache"},
    )


@router.get("/{document_id}/source")
@inject
async def download_data_document_source(
    document_id: int,
    session_factory: "sessionmaker" = Depends(lambda: di["session_factory"]),
):
    """Download the original file.

    Parameters
    ----------
    document_id : int
        Primary key.
    session_factory : sessionmaker
        Session factory from the DI container.

    Returns
    -------
    FileResponse
        The file as an attachment.
    """
    return _serve_source(document_id, "attachment", session_factory)


@router.get("/{document_id}/source/view")
@inject
async def view_data_document_source(
    document_id: int,
    session_factory: "sessionmaker" = Depends(lambda: di["session_factory"]),
):
    """Serve the original file for inline viewing (iframe or fetch).

    Parameters
    ----------
    document_id : int
        Primary key.
    session_factory : sessionmaker
        Session factory from the DI container.

    Returns
    -------
    FileResponse
        The file, inline.
    """
    return _serve_source(document_id, "inline", session_factory)
