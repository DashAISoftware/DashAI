from fastapi import FastAPI
from Models.enums.squema_types import SquemaTypes
from configObject import ConfigObject

app = FastAPI()
session_info = {}

@app.post("/dataset/upload/{dataset}")
async def upload_dataset(dataset: str):
    session_id = 0
    print(dataset)
    session_info[session_id] = dataset 
    return {"models": ["knn","naive_bayes","random_forest"]}

@app.post("/dataset/upload/{dataset_id}")
async def upload_dataset(dataset_id: int):
    session_id = 0
    session_info[session_id] = dataset_id 
    return {"models": ["knn","naive_bayes","random_forest"]}

@app.get("/selectModel/{model_name}")
def select_model(model_name : str):
    """
    It returns the squema of the selected model
    """
    try:
        return ConfigObject().get_squema(SquemaTypes.model, model_name)
    except:
        return f"Squema for model {model_name} not found"

@app.post("/selectedParameters/{model_name}")
async def execute_model(model_name : str, parameters_json):
    #execution_id = set_execution(model_name, parameters_json) # TODO: Create this method
    #return execution_id
    pass

@app.post("/experiment/run/{session_id}")
async def run_experiment(session_id: int):
    return session_id

@app.get("/experiment/results/{session_id}")
async def get_results(session_id: int):
    return {"knn": {"accuracy": 0.8, "precision": 0.7, "recall": 0.9}}
