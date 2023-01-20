import uvicorn
from fastapi import FastAPI, File, UploadFile, Request, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from Models.enums.squema_types import SquemaTypes
from TaskLib.task.taskMain import Task
from TaskLib.task.numericClassificationTask import NumericClassificationTask
from TaskLib.task.textClassificationTask import TextClassificationTask
from Models.classes.getters import filter_by_parent
from configObject import ConfigObject
from Models.classes.getters import get_model_params_from_task
from Dataloaders.csvDataLoader import CSVDataLoader
from uuid import uuid4
import zipfile
import json
import os
import io

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
#main_task: Task

def generate_dataset_id(dataset_list):
    """
        generate unique ID for datasets
    """
    dataset_id = str(uuid4())
    for name in list(dataset_list.keys()):
        if dataset_id == name:
            return generate_dataset_id(dataset_list)
    return dataset_id

@app.get("/info")
async def get_state():
    return {"state":"online"}

@app.get("/showTasks")
async def show_tasks():
    # TODO: implement show tasks to select
    return None

@app.post("/selectTask")
async def select_tasks(task_name: str):
    session_id = 0
    session_info[session_id] = {
            "task_name": task_name,
            "task": Task.createTask(task_name),
            "splits": False # default value
    }
    return session_info

@app.get("/selectDatasets")
def select_dataset():
    try:
        datasets_list = open("dataset_list.json")
        return json.load(dataset_list)
    except:
        return {"message": "Datasets can't be loaded"}

@app.post("/dataset/upload/{session_id}")
async def upload_dataset(session_id: int, dataset_name: str = None, file: UploadFile = File(None), url: str = None):
    with open("dataset_list.json", "r") as f:
        dataset_list = json.load(f)
    if dataset_name is None: 
        dataset_name = generate_dataset_id(dataset_list)
    else:
        for name in list(dataset_list.keys()):
            if dataset_name == name: # check for existing dataset name
                return {"message": f"A dataset with name {dataset_name} already exist."}
    folder_path = os.path.dirname(os.getcwd())+"/datasets/"+dataset_name
    task = session_info[session_id]["task_name"]
    try:
        if url:
            if url.split('.')[-1] == 'csv':
                    CSVDataLoader.load_data(folder_path, url)

                    # TODO: add other formats (json, text, parquet, etc)
        if file: 
            if task == "image" or task == "audio": # Reference names for images and audio tasks
                if file.content_type == "application/zip":
                    with zipfile.ZipFile(io.BytesIO(file.file.read()), 'r') as zip_file:
                        zip_file.extractall(path=folder_path)
                    if any(s in os.listdir(folder_path) for s in ["train", "test", "val", "validation"]):
                        session_info[session_id]["splits"] = True # Check for split folders

                    # TODO: call to images or audio dataloader

                    session_info[session_id]["input_type"] = "non-tabular"
                else:
                    return {"message": f"For the task '{task}' a .zip file is required."}
            else:
                os.mkdir(folder_path)
                for file in files:
                    contents = file.file.read()
                    with open(f'{folder_path}/{file.filename}', 'wb') as f:
                        f.write(contents)
                if os.path.splitext(file.filename)[1] == '.csv':
                    CSVDataLoader.load_data(folder_path)
                
                # TODO: add other formats (json, text, parquet, etc)

                session_info[session_id]["input_type"] = "tabular"

        dataset_list[dataset_name] = folder_path
        with open("dataset_list.json", "w") as f:
            json.dump(dataset_list, f)
        session_info[session_id]["dataset"] = dataset_name
    except:
        return {"message": "Couldn't read file."}

@app.get("/dataset/settings/{session_id}")
async def config_params_dataset(session_id: int):
    """
    Send to client the schemas with the datasets configuration parameters
    """
    data_type = session_info[session_id]["input_type"]
    schemas_path = "Dataloaders/dataloaders_schemas"
    if data_type == "tabular": # Tabular datasets requires configuration
        with open(schemas_path+"tabular_datasets.json", "r") as f:
            schema = json.load(f)
        return schema
    elif data_type == "non-tabular" and not session_info[session_id]["splits"]:
        with open(schemas_path+"splits_settings.json", "r") as f:
            schema = json.load(f)
        return schema # Non tabular dataset without splits, have to set splits
    else:
        return None # Non tabular dataset with defined splits, no configure required

@app.post("/dataset/settings/{session_id}")
async def configure_dataset(session_id: int, payload: dict = Body(...)):
    # TODO: receive parameters to build dataset to use
    return {"message": "To be implemented"}

@app.get("/dataset/summary/{session_id}")
async def dataset_stats(session_id: int):
    # TODO: send to client the stats of dataset
    return {"message": "To be implemented"}

@app.post("/dataset/upload/{dataset_id}")
async def upload_dataset(dataset_id: int):
    return {"message": "To be implemented"}

@app.get("/dataset/task_name/{session_id}")
async def get_task_name(session_id: int):
    session_id = 0 # TODO Get session_id from user
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

@app.get("/selectModel/{model_name}")
def select_model(model_name : str): # TODO: Generalize this function to any kind of config object
    """
    It returns the squema of the selected model
    """
    try:
        return ConfigObject().get_squema(SquemaTypes.model, model_name)
    except:
        return f"Squema for {model_name} not found"

@app.post("/selectedParameters/{model_name}")
async def execute_model(model_name : str, payload: dict = Body(...)):
    session_id = 0 # TODO Get session_id from user
    main_task = session_info[session_id]["task"]
    execution_id = 0 # TODO: generate unique ids for an experiment
    main_task.set_executions(model_name, payload)
    return execution_id

@app.post("/upload")
async def upload_test(file: UploadFile = File()):
    try:
        contents = file.file.read()
        with open(file.filename, 'wb') as f:
            f.write(contents)
    except:
        return {"message": "There was an error uploading the file"}
    finally:
        file.file.close()

    return {"message": f"Succesfully uploaded {file.filename}"}
    
@app.post("/experiment/run/{session_id}")
async def run_experiment(session_id: int):
    session_id = 0 # TODO Get session_id from user
    main_task = session_info[session_id]["task"]
    main_task.run_experiments(session_info[session_id]["dataset"])
    return session_id

@app.get("/experiment/results/{session_id}")
async def get_results(session_id: int):
    session_id = 0 # TODO Get session_id from user
    main_task = session_info[session_id]["task"]
    return main_task.experimentResults

@app.get("/play/{session_id}/{execution_id}/{input}")
async def generate_prediction(session_id: int, execution_id: int, input_data: str):
    session_id = 0 # TODO Get session_id from user
    execution_id = 0 # TODO Get execution_id from user
    main_task = session_info[session_id]["task"]
    return str(main_task.get_prediction(execution_id, input_data))

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)