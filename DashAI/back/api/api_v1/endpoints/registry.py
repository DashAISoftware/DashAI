import logging
from typing import Union

from fastapi import APIRouter, status
from fastapi.exceptions import HTTPException

from DashAI.back.core.config import name_registry_mapping

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)

router = APIRouter()


@router.get("/relationship/{source_type}/{task_name}")
async def get_objects(source_type: str, task_name: str):
    """
    Returns all the available objects of type source_type and its schemas,
    related to the task with name task_name.
    
    Returns
    -------
    List[JSON]
        List of objects JSONs
    """
    source_registry = name_registry_mapping[source_type]
    related_objects = source_registry.task_to_components(task_name)
    if not related_objects:
        return []
    all_objects = [
        source_registry[object_name].get_schema()
        for object_name in related_objects
    ]
    return all_objects

@router.get("/inheritance/{source_type}/")
async def get_objects(source_type: str, parent_name: Union[str, None] = None):
    """
    Returns all the available objects of type source_type and its schemas,
    that inherits from the object with name parent_name.
    If no parent_name is given, return all the available objects of the
    specified source_type.
    
    Returns
    -------
    List[JSON]
        List of objects JSONs
    """
    source_registry = name_registry_mapping[source_type]
    related_objects = source_registry.parent_to_components(parent_name)
    if not related_objects:
        return []
    all_objects = [
        source_registry[object_name].get_schema()
        for object_name in related_objects
    ]
    return all_objects


@router.post("/", status_code=status.HTTP_201_CREATED)
async def upload_dataloader():
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Method not implemented"
    )


@router.delete("/")
async def delete_dataloader():
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Method not implemented"
    )


@router.patch("/")
async def update_dataloader():
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Method not implemented"
    )
