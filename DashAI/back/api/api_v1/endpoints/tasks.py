import logging

from fastapi import APIRouter, status
from fastapi.exceptions import HTTPException

from DashAI.back.core.config import task_registry

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)

router = APIRouter()


@router.get("/")
async def get_tasks():
    """
    Returns all the available task and its schemas.

    Returns
    -------
    List[JSON]
        List of task JSONs
    """

    register_tasks = task_registry.registry
    if not register_tasks:
        return []
    all_tasks = [task_cls.get_schema() for _, task_cls in register_tasks.items()]
    return all_tasks


@router.post("/", status_code=status.HTTP_201_CREATED)
async def upload_task():
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Method not implemented",
    )


@router.delete("/")
async def delete_task():
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Method not implemented",
    )


@router.patch("/")
async def update_task():
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Method not implemented",
    )
