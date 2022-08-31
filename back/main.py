from fastapi import FastAPI, File, UploadFile
from Models.enums.squema_types import SquemaTypes
from Models.classes.getters import filter_by_parent
from configObject import ConfigObject
import json

import json

app = FastAPI()
session_info = {}

@app.get("/info")
async def get_state():
    return {"state":"online"}

@app.post("/dataset/upload/")
async def upload_dataset(file: UploadFile = File(...)):
    print("INSIDE")
    session_id = 0
    try:
        dataset = json.load(file.file)
        print(dataset)
        session_info[session_id] = dataset
        session_info["task_name"] = dataset["task_info"]
    except:
        return {"message": "Couldn't read file."}
    finally:
        file.file.close()
    return {"models": ["knn","naive_bayes","random_forest"]}

@app.post("/dataset/upload/{dataset_id}")
async def upload_dataset(dataset_id: int):
    session_id = 0
    session_info[session_id] = dataset_id 
    return {"models": ["knn","naive_bayes","random_forest"]}

@app.get("/models/")
def available_models():
    """
    It returns all the classes that inherits from Model class
    """
    task_name = session_info["task_name"]
    model_class_name = f"{task_name[:-4]}Model"
    dict = filter_by_parent(model_class_name)
    return list(dict.keys())

@app.get("/selectModel/{model_name}")
def select_model(model_name : str):
    """
    It returns the squema of the selected model
    """
    try:
        return ConfigObject().get_squema(SquemaTypes.model, model_name)
    except:
        return f"Squema for {model_name} not found"

@app.post("/selectedParameters/{model_name}")
async def execute_model(model_name : str, parameters_json):
    pass
    #execution_id = set_execution(model_name, parameters_json) # TODO: Create this method
    #return execution_id

@app.post("/experiment/run/{session_id}")
async def run_experiment(session_id: int):
    return session_id

@app.get("/experiment/results/{session_id}")
async def get_results(session_id: int):
    return {"knn": {"accuracy": 0.8, "precision": 0.7, "recall": 0.9}}
