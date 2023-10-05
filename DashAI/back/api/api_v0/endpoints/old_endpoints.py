import json

from fastapi import APIRouter, Body

from DashAI.back.api.api_v0.endpoints.session_class import session_info
from DashAI.back.config_object import ConfigObject
from DashAI.back.core.enums.squema_types import SquemaTypes
from DashAI.back.models.classes.getters import filter_by_parent

router = APIRouter()


@router.get("/select/{schema_type}/{model_name}")
def select_schema(schema_type: str, model_name: str):
    """Return the squema of any configurable object."""
    try:
        return ConfigObject().get_squema(SquemaTypes[schema_type], model_name)
    except (FileNotFoundError, json.decoder.JSONDecodeError):
        return f"Squema for {model_name} not found"


@router.post("/dataset/upload/{dataset_id}")
async def upload_dataset_id(dataset_id: int):
    return {"message": dataset_id + " to be implemented in the future."}


@router.get("/dataset/task_name/{session_id}")
async def get_task_name(session_id: int):
    return session_info.task_name


@router.get("/getChildren/{parent}")
def get_children(parent):
    """Return all the classes that inherits from the Model selected."""
    try:
        return list(filter_by_parent(parent).keys())
    except TypeError:
        return f"{parent} not found"


@router.get("/selectModel/{model_name}")
def select_model(model_name: str):
    # TODO: Generalize this function to any kind of config object
    """Return the squema of the selected model."""
    try:
        return ConfigObject().get_squema(SquemaTypes.model, model_name)
    except (FileNotFoundError, json.decoder.JSONDecodeError):
        return f"Squema for {model_name} not found"


@router.post("/selectedParameters/{model_name}")
async def execute_model(model_name: str, payload: dict = Body(...)):
    return 0


@router.post("/experiment/run/{session_id}")
async def run_experiment(session_id: int):
    return 0


@router.get("/experiment/results/{session_id}")
async def get_results(session_id: int):
    main_task = session_info.task
    return main_task.experimentResults


@router.get("/play/{session_id}/{execution_id}/{input}")
async def generate_prediction(session_id: int, execution_id: int, input_data: str):
    execution_id = 0  # TODO Get execution_id from user
    main_task = session_info.task
    return str(main_task.get_prediction(execution_id, input_data))
