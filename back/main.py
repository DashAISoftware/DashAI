import uvicorn
from fastapi import FastAPI, File, UploadFile, Request, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from Models.enums.squema_types import SquemaTypes
from TaskLib.task.taskMain import Task
from TaskLib.task.numericClassificationTask import NumericClassificationTask
from TaskLib.task.textClassificationTask import TextClassificationTask
from configObject import ConfigObject
from Models.classes.getters import get_model_params_from_task
import json

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

@app.get("/info")
async def get_state():
    return {"state":"online"}

@app.post("/dataset/upload/")
async def upload_dataset(file: UploadFile = File(...)):
    print("INSIDE")
    session_id = 0
    try:
        dataset = json.load(file.file)
        #print(dataset)
        session_info[session_id] = dataset #TODO Quien genera/maneja las ids? Como el front sabe cual es la id
        session_info["task_name"] = dataset["task_info"]["task_type"] # TODO Como se asocia session_id con task_name y task?
        session_info["task"] = Task.createTask(session_info["task_name"])
    except:
        return {"message": "Couldn't read file."}
    finally:
        file.file.close()
    print
    return get_model_params_from_task(session_info["task_name"])

@app.post("/dataset/upload/{dataset_id}")#TODO Como el front sabe cuales son las ids de los datasets ya disponibles?
async def upload_dataset(dataset_id: int):
    session_id = 0
    session_info[session_id] = dataset_id 
    return {"models": ["knn","naive_bayes","random_forest"]}

@app.get("/models/{model_name}") # Esto no deberia ser task_name en vez de model_name?
def available_models(model_name):
    """
    It returns all the classes that inherits from the Model selected
    """
    try:
        return get_model_params_from_task(model_name)# Es buena idea retornar distintos status_code, por ejemplo
    except:                                          # si la respuesta contiene error, enviar status = 400
        return f"{model_name} not found"

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
async def execute_model(model_name : str, payload: dict = Body(...)):
    print("MODEL: " + model_name)
    print("TASK: " + session_info["task_name"])
    print(session_info["task"])
    print("JSON:")
    print(payload)
    # print("DATASET: ")
    # print(session_info[0])
    main_task = session_info["task"]
    execution_id = 0
    main_task.set_executions([model_name], payload) # TODO: Make it return an execution id
    print(main_task.executions)
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
    main_task = session_info["task"]
    main_task.run_experiments(session_info[session_id])
    print(main_task.experimentResults)
    return session_id

@app.get("/experiment/results/{session_id}")
async def get_results(session_id: int):
    return {"knn": {"accuracy": 0.8, "precision": 0.7, "recall": 0.9}}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)