import logging
from typing import TYPE_CHECKING, List

from fastapi import APIRouter, Depends, HTTPException, status

if TYPE_CHECKING:
    from sqlalchemy.orm import sessionmaker
from kink import di, inject
from sqlalchemy import exc, select

from DashAI.back.api.api_v1.schemas.folders_params import (
    Folder as FolderSchema,
)
from DashAI.back.api.api_v1.schemas.folders_params import (
    FolderCreateParams,
    FolderUpdateParams,
)
from DashAI.back.dependencies.database.models import Folder

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/", response_model=List[FolderSchema])
@inject
async def get_folders(
    session_factory: "sessionmaker" = Depends(lambda: di["session_factory"]),
):
    """Retrieve all folders ordered by name."""
    with session_factory() as db:
        try:
            folders = db.query(Folder).order_by(Folder.name).all()
        except exc.SQLAlchemyError as e:
            logger.exception(e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal database error",
            ) from e
    return folders


@router.post("/", response_model=FolderSchema, status_code=status.HTTP_201_CREATED)
@inject
async def create_folder(
    params: FolderCreateParams,
    session_factory: "sessionmaker" = Depends(lambda: di["session_factory"]),
):
    """Create a new folder."""
    if not params.name or not params.name.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Folder name cannot be empty",
        )
    with session_factory() as db:
        try:
            existing = db.execute(
                select(Folder.id).where(Folder.name == params.name.strip())
            ).scalar()
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"A folder with the name '{params.name}' already exists",
                )
            folder = Folder(name=params.name.strip())
            db.add(folder)
            db.commit()
            db.refresh(folder)
            return folder
        except HTTPException:
            raise
        except exc.IntegrityError as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"A folder with the name '{params.name}' already exists",
            ) from e
        except exc.SQLAlchemyError as e:
            db.rollback()
            logger.exception(e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal database error",
            ) from e


@router.patch("/{folder_id}", response_model=FolderSchema)
@inject
async def update_folder(
    folder_id: int,
    params: FolderUpdateParams,
    session_factory: "sessionmaker" = Depends(lambda: di["session_factory"]),
):
    """Rename a folder."""
    if not params.name or not params.name.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Folder name cannot be empty",
        )
    with session_factory() as db:
        folder = db.get(Folder, folder_id)
        if folder is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Folder not found"
            )
        new_name = params.name.strip()
        if new_name == folder.name:
            return folder
        exists = db.execute(
            select(Folder.id).where(Folder.name == new_name, Folder.id != folder_id)
        ).scalar()
        if exists:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Folder name already exists",
            )
        folder.name = new_name
        try:
            db.commit()
            db.refresh(folder)
            return folder
        except exc.IntegrityError as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Folder name already exists",
            ) from e
        except exc.SQLAlchemyError as e:
            db.rollback()
            logger.exception(e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal database error",
            ) from e


@router.delete("/{folder_id}", status_code=status.HTTP_204_NO_CONTENT)
@inject
async def delete_folder(
    folder_id: int,
    session_factory: "sessionmaker" = Depends(lambda: di["session_factory"]),
):
    """Delete a folder. Datasets in the folder are moved to no folder (SET NULL)."""
    with session_factory() as db:
        folder = db.get(Folder, folder_id)
        if folder is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Folder not found"
            )
        try:
            for dataset in folder.datasets:
                dataset.folder_id = None
            db.delete(folder)
            db.commit()
        except exc.SQLAlchemyError as e:
            db.rollback()
            logger.exception(e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal database error",
            ) from e
