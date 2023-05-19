import logging

from fastapi import APIRouter, status
from fastapi.exceptions import HTTPException

from DashAI.back.core.config import dataloader_registry

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)

router = APIRouter()


@router.get("/{task_name}")
async def get_dataloaders(task_name: str):
    """
    Returns all the available dataloaders and its schemas.
    Returns
    -------
    List[JSON]
        List of dataloaders JSONs
    """

    register_dataloaders = dataloader_registry.task_to_components(task_name)
    if not register_dataloaders:
        return []
    all_dataloaders = [
        dataloader_registry[dataloader_name].get_schema()
        for dataloader_name in register_dataloaders
    ]
    return all_dataloaders


@router.post("/", status_code=status.HTTP_201_CREATED)
async def upload_dataloader():
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Method not implemented",
    )


@router.delete("/")
async def delete_dataloader():
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Method not implemented",
    )


@router.patch("/")
async def update_dataloader():
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Method not implemented",
    )
