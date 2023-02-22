import json

import uvicorn
from fastapi import Body, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from DashAI.back.config_object import ConfigObject
from DashAI.back.database import db
from DashAI.back.models.classes.getters import filter_by_parent
from DashAI.back.models.enums.squema_types import SquemaTypes
from DashAI.back.routers import datasets, experiments
from DashAI.back.routers.session_class import session_info

# TODO These imports should be removed because they are unused, but currently needed.
from DashAI.back.tasks.tabular_classification_task import TabularClassificationTask
from DashAI.back.tasks.task import Task
from DashAI.back.tasks.text_classification_task import TextClassificationTask
from DashAI.back.tasks.translation_task import TranslationTask

app = FastAPI(title="DashAI")

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


@app.get("/select/{schema_type}/{model_name}")
def select_schema(schema_type: str, model_name: str):
    """
    It returns the squema of any configurable object
    """
    try:
        return ConfigObject().get_squema(SquemaTypes[schema_type], model_name)
    except (FileNotFoundError, json.decoder.JSONDecodeError):
        return f"Squema for {model_name} not found"


@app.post("/selectedParameters/{model_name}")
async def execute_model(model_name: str, payload: dict = Body(...)):
    main_task = session_info.task
    execution_id = 0  # TODO: generate unique ids for an experiment
    main_task.set_executions(model_name, payload)
    return execution_id


@app.get("/play/{session_id}/{execution_id}/{input}")
async def generate_prediction(session_id: int, execution_id: int, input: str):
    main_task = session_info.task
    return str(main_task.get_prediction(0, input))


if __name__ == "__main__":
    db.Base.metadata.create_all(db.engine)
    uvicorn.run(app, host="127.0.0.1", port=8000)
