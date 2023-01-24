import json

import uvicorn
from configObject import ConfigObject
from fastapi import Body, FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from Models.classes.getters import filter_by_parent, get_model_params_from_task
from Models.enums.squema_types import SquemaTypes

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

session_info = {}
# main_task: Task


@app.get("/info")
async def get_state():
    return {"state": "online"}


@app.post("/dataset/upload/")
async def upload_dataset(file: UploadFile = File(...)):
    session_id = 0  # TODO: generate unique ids
    task_name = ""
    try:
        dataset = json.load(file.file)
        task_name = dataset["task_info"]["task_type"]
        session_info[session_id] = {
            "dataset": dataset,
            "task_name": task_name,
            # TODO Task throw exception if createTask fails
            "task": Task.createTask(task_name),
        }
    except json.decoder.JSONDecodeError:
        return {"message": "Couldn't read file."}
    finally:
        file.file.close()
    # TODO give session_id to user
    return get_model_params_from_task(task_name)


@app.post("/dataset/upload/{dataset_id}")
async def upload_dataset_id(dataset_id: int):
    return {"message": dataset_id + " to be implemented in the future."}


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


@app.post("/upload")
async def upload_test(file: UploadFile = File()):
    try:
        contents = file.file.read()
        with open(file.filename, "wb") as f:
            f.write(contents)
    except IOError:
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


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
