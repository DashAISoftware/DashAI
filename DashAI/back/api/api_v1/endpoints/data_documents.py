"""Endpoints for the persistent documents of the Data module.

Mounted at ``/api/v1/documents``. The session scoped RAG documents keep their
own router at ``/api/v1/document`` until branch 5 retires it.
"""

import logging
import os
from pathlib import Path
from typing import TYPE_CHECKING, List

from fastapi import APIRouter, Depends, Response, status
from fastapi.exceptions import HTTPException
from kink import di, inject
from pydantic import ValidationError
from sqlalchemy import exc, select

from DashAI.back.api.api_v1.schemas.data_documents_params import (
    DataDocumentCreateParams,
    DataDocumentSchema,
    DataDocumentUpdateParams,
)
from DashAI.back.core.enums.status import DocumentStatus
from DashAI.back.dataloaders.classes.dataloader import (
    DataKindMismatchError,
    require_data_kind,
)
from DashAI.back.dependencies.database.models import DataDocument, Folder
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
    """Delete a document row and, once that commits, its folder on disk.

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
