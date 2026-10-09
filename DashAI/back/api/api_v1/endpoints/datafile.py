"""Datafile management endpoints."""

import json
import logging
import os
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List

from fastapi import APIRouter, Depends, status
from fastapi.exceptions import HTTPException
from kink import di
from pydantic import BaseModel
from sqlalchemy import exc

from DashAI.back.core.enums.status import DatafileStatus
from DashAI.back.dependencies.database.models import Datafile

if TYPE_CHECKING:
    from sqlalchemy.orm import sessionmaker

    from DashAI.back.dependencies.registry import ComponentRegistry

log = logging.getLogger(__name__)
router = APIRouter()


def _row_to_dict(row: Datafile) -> Dict[str, Any]:
    return {
        "id": row.id,
        "source_name": row.source_name,
        "dataset_id": row.dataset_id,
        "name": row.name,
        "local_path": row.local_path,
        "status": row.status.value,
        "error_message": row.error_message,
        "size_bytes": row.size_bytes,
        "description": row.description,
        "tags": json.loads(row.tags) if row.tags else [],
        "source_url": row.source_url,
        "created": row.created.isoformat() if row.created else None,
        "last_modified": row.last_modified.isoformat() if row.last_modified else None,
    }


class CreateDownloadRequest(BaseModel):
    source_name: str
    dataset_id: str
    name: str
    description: str = ""
    tags: list[str] = []
    source_url: str = ""


@router.get("/", response_model=List[Dict[str, Any]])
async def list_downloads(
    session_factory: "sessionmaker" = Depends(lambda: di["session_factory"]),
) -> List[Dict[str, Any]]:
    """Return all datafile records."""
    with session_factory() as db:
        rows = db.query(Datafile).order_by(Datafile.created.asc()).all()
        return [_row_to_dict(r) for r in rows]


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=Dict[str, Any])
async def create_download(
    body: CreateDownloadRequest,
    session_factory: "sessionmaker" = Depends(lambda: di["session_factory"]),
    registry: "ComponentRegistry" = Depends(lambda: di["component_registry"]),
) -> Dict[str, Any]:
    """Create a Datafile record.

    If a record for (source_name, dataset_id) already exists and its status is
    READY or DOWNLOADING, it is returned immediately. If status is ERROR the
    record is reset to DOWNLOADING so the caller can re-enqueue the job.
    """
    sources = registry._registry.get("DatasetSource", {})
    if body.source_name not in sources:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"DatasetSource '{body.source_name}' not found.",
        )

    with session_factory() as db:
        existing = (
            db.query(Datafile)
            .filter(
                Datafile.source_name == body.source_name,
                Datafile.dataset_id == body.dataset_id,
            )
            .first()
        )
        if existing is not None:
            if existing.status == DatafileStatus.READY:
                return _row_to_dict(existing)
            if existing.status == DatafileStatus.DOWNLOADING:
                return _row_to_dict(existing)
            # ERROR, allow retry: reset to downloading
            existing.status = DatafileStatus.DOWNLOADING
            existing.error_message = None
            existing.local_path = None
            existing.name = body.name
            existing.description = body.description
            existing.tags = json.dumps(body.tags)
            existing.source_url = body.source_url or None
            try:
                db.commit()
                db.refresh(existing)
            except exc.SQLAlchemyError as e:
                log.exception(e)
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="DB error resetting download.",
                ) from e
            row = existing
        else:
            row = Datafile(
                source_name=body.source_name,
                dataset_id=body.dataset_id,
                name=body.name,
                description=body.description,
                tags=json.dumps(body.tags),
                source_url=body.source_url or None,
                status=DatafileStatus.DOWNLOADING,
            )
            db.add(row)
            try:
                db.commit()
                db.refresh(row)
            except exc.SQLAlchemyError as e:
                log.exception(e)
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="DB error creating download record.",
                ) from e

        return _row_to_dict(row)


@router.get("/{datafile_id}", response_model=Dict[str, Any])
async def get_download(
    datafile_id: int,
    session_factory: "sessionmaker" = Depends(lambda: di["session_factory"]),
) -> Dict[str, Any]:
    """Return a single datafile record by id."""
    with session_factory() as db:
        row = db.get(Datafile, datafile_id)
        if row is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Datafile {datafile_id} not found.",
            )
        return _row_to_dict(row)


@router.delete("/{datafile_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_download(
    datafile_id: int,
    session_factory: "sessionmaker" = Depends(lambda: di["session_factory"]),
) -> None:
    """Delete a datafile record and its cached files."""
    import shutil

    with session_factory() as db:
        row = db.get(Datafile, datafile_id)
        if row is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Datafile {datafile_id} not found.",
            )
        local_path = row.local_path
        try:
            db.delete(row)
            db.commit()
        except exc.SQLAlchemyError as e:
            log.exception(e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="DB error deleting download record.",
            ) from e

    if local_path and os.path.exists(local_path):
        shutil.rmtree(local_path, ignore_errors=True)


@router.get("/{datafile_id}/files", response_model=List[str])
async def list_files(
    datafile_id: int,
    session_factory: "sessionmaker" = Depends(lambda: di["session_factory"]),
) -> List[str]:
    """Return the list of files in a ready datafile directory."""
    with session_factory() as db:
        row = db.get(Datafile, datafile_id)
        if row is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Datafile {datafile_id} not found.",
            )
        if row.status != DatafileStatus.READY or not row.local_path:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Download is not ready yet.",
            )
        local_path = row.local_path

    path = Path(local_path)
    if not path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Download directory not found on disk.",
        )
    files = sorted(
        str(p.relative_to(path))
        for p in path.rglob("*")
        if p.is_file()
        and not any(part.startswith(".") for part in p.relative_to(path).parts)
    )
    return files
