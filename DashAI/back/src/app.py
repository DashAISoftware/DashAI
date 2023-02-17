import json

import uvicorn
from base.base_task import BaseTask
from fastapi import Body, FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from models import SVC, KNeighborsClassifier, RandomForestClassifier
from models.classes.getters import filter_by_parent, get_model_params_from_task
from models.enums.squema_types import SquemaTypes
from registry.model_registry import ModelRegistry
from registry.task_registry import TaskRegister
from tasks.tabular_classification_task import TabularClassificationTask
from tasks.text_classification_task import TextClassificationTask

from DashAI.back.src.config_object import ConfigObject

task_register = TaskRegister(
    default_tasks=[TabularClassificationTask, TextClassificationTask]
)

model_register = ModelRegistry(
    task_register, default_models=[SVC, KNeighborsClassifier, RandomForestClassifier]
)


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

session_info = {}
# main_task: Task


@app.get("/info")
async def get_state():
    return {"state": "online"}


@app.get("/dataset/{id}")
async def get_dataset(id: str):

@app.put("/dataset/")

@app.delete("/dataset/")
async def get_dataset(id: str):
    raise HTTPError('No se puede eliminar un datasset')

RESTfult 
@app.post("/dataset")
async def upload_dataset(file: UploadFile = File(...)):
    session_id = 0  # TODO: generate unique ids
    task_name = ""
    try:
        dataset = json.load(file.file)
        task_name = dataset["task_info"]["task_type"]
        session_info[session_id] = {
            "dataset": dataset,
            "task_name": task_name,
            "task": BaseTask.createTask(task_name),
        }
    except:
        return {"message": "Couldn't read file."}
    finally:
        file.file.close()
    return get_model_params_from_task(task_name)  # TODO give session_id to user


@app.post("/dataset/upload/{dataset_id}")
async def upload_dataset(dataset_id: int):
    return {"message": "To be implemented"}


@app.get("/dataset/task_name/{session_id}")
async def get_task_name(session_id: int):
    session_id = 0  # TODO Get session_id from user
    return session_info[session_id]["task_name"]


@app.get("/getChildren/{parent}")
def get_children(parent):
    """
    It returns all the classes that inherits from the Model selected
    """
    try:
        return list(filter_by_parent(parent).keys())
    except:
        return f"{parent} not found"

@app.get("/model/{id}?model_type==boosting")
def get_model(id):
    return models





@app.get("/selectModel/{model_name}")
def select_model(
    model_name: str,
):  # TODO: Generalize this function to any kind of config object
    """
    It returns the squema of the selected model
    """
    try:
        return ConfigObject().get_squema(SquemaTypes.model, model_name)
    except:
        return f"Squema for {model_name} not found"


@app.post("/selectedParameters/{model_name}")
async def execute_model(model_name: str, payload: dict = Body(...)):
    session_id = 0  # TODO Get session_id from user
    main_task = session_info[session_id]["task"]
    execution_id = 0  # TODO: generate unique ids for an experiment
    main_task.set_executions(model_name, payload)
    return execution_id


@app.post("/upload")
async def upload_test(file: UploadFile = File()):
    try:
        contents = file.file.read()
        with open(file.filename, "wb") as f:
            f.write(contents)
    except:
        return {"message": "There was an error uploading the file"}
    finally:
        file.file.close()

    return {"message": f"Succesfully uploaded {file.filename}"}


@app.post("/experiment/run/{session_id}")
async def run_experiment(session_id: int):
    session_id = 0  # TODO Get session_id from user
    main_task = session_info[session_id]["task"]
    main_task.run_experiments(session_info[session_id]["dataset"])
    return session_id


@app.get("/experiment/results/{session_id}")
async def get_results(session_id: int):
    session_id = 0  # TODO Get session_id from user
    main_task = session_info[session_id]["task"]
    return main_task.experimentResults


@app.get("/play/{session_id}/{execution_id}/{input}")
async def generate_prediction(session_id: int, execution_id: int, input_data: str):
    session_id = 0  # TODO Get session_id from user
    execution_id = 0  # TODO Get execution_id from user
    main_task = session_info[session_id]["task"]
    return str(main_task.get_prediction(execution_id, input_data))
