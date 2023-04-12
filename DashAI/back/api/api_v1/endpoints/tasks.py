from collections import defaultdict
import json
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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No tasks found"
        )
    all_tasks = defaultdict(dict)
    # TODO: get the task schema from task
    tasks_schema = json.load(open('DashAI/back/tasks/tasks_schemas/tasks.json', 'r'))
    for task_name in register_tasks.keys():
        for task_schema in tasks_schema['tasks']:
            if task_schema['class'] == task_name:
                all_tasks[task_name] = task_schema
    return all_tasks

@router.post("/", status_code=status.HTTP_201_CREATED)
async def upload_task():
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Method not implemented"
    )

@router.delete("/")
async def delete_task():
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Method not implemented"
    )

@router.patch("/")
async def update_task():
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Method not implemented"
    )