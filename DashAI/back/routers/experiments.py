from fastapi import APIRouter, status, Form, UploadFile, File
import pydantic
from fastapi.exceptions import HTTPException
from fastapi.encoders import jsonable_encoder
import os
from Models.classes.getters import get_model_params_from_task
from Database import db, models
from sqlalchemy import exc
from TaskLib.task.taskMain import Task
from routers.session_class import session_info

router = APIRouter()

current_task = None

@router.post("/experiment/run/{session_id}")
async def run_experiment():
    main_task = session_info.task
    main_task.run_experiments(session_info.dataset)
    return 0


@router.get("/experiment/results/{session_id}")
async def get_results():
    main_task = session_info.task
    return main_task.experimentResults