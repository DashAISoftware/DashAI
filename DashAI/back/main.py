import json
import os
import pathlib

import uvicorn
from configObject import ConfigObject
from Database import db
from fastapi import Body, FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from Models.classes.getters import filter_by_parent, get_model_params_from_task

# TODO see how to avoid importing this
from Models.classes.sklearnLikeModel import SklearnLikeModel
from Models.enums.squema_types import SquemaTypes
from routers import datasets, experiments
from routers.session_class import session_info

# TODO These imports should be removed because they are unused, but currently needed.
from TaskLib.task.numericClassificationTask import NumericClassificationTask
from TaskLib.task.taskMain import Task
from TaskLib.task.textClassificationTask import TextClassificationTask
from TaskLib.task.TranslationTask import TranslationTask

app = FastAPI()

origins = [
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(datasets.router)
app.include_router(experiments.router)


@app.get("/info")
async def get_state():
    return {"state": "online"}


# CHECK USE
@app.get("/getChildren/{parent}")
def get_children(parent):
    """
    It returns all the classes that inherits from the Model selected
    """
    try:
        return list(filter_by_parent(parent).keys())
    except TypeError:
        return f"{parent} not found"


@app.get("/selectModel/{model_name}")
def select_model(
    model_name: str,
):  # TODO: Generalize this function to any kind of config object
    """
    It returns the squema of the selected model
    """
    try:
        return ConfigObject().get_squema(SquemaTypes.model, model_name)
    except (FileNotFoundError, json.decoder.JSONDecodeError):
        return f"Squema for {model_name} not found"


@app.post("/selectedParameters/{model_name}")
async def execute_model(model_name: str, payload: dict = Body(...)):
    session_id = 0  # TODO Get session_id from user
    main_task = session_info[session_id]["task"]
    execution_id = 0  # TODO: generate unique ids for an experiment
    main_task.set_executions(model_name, payload)
    return execution_id


@app.get("/play/{session_id}/{execution_id}/{input}")
async def generate_prediction(session_id: int, execution_id: int, input_data: str):
    session_id = 0  # TODO Get session_id from user
    execution_id = 0  # TODO Get execution_id from user
    main_task = session_info[session_id]["task"]
    return str(main_task.get_prediction(execution_id, input_data))


if __name__ == "__main__":
    db.Base.metadata.create_all(db.engine)
    uvicorn.run(app, host="127.0.0.1", port=8000)
