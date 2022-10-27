import uvicorn
from fastapi import FastAPI, File, UploadFile, Body
from fastapi.middleware.cors import CORSMiddleware
from Models.enums.squema_types import SquemaTypes
from TaskLib.task.taskMain import Task
from TaskLib.task.numericClassificationTask import NumericClassificationTask
from TaskLib.task.textClassificationTask import TextClassificationTask
from Database import db, models
from Models.classes.getters import filter_by_parent
from configObject import ConfigObject
from Models.classes.getters import get_model_params_from_task
import json
import os

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

# TODO delete this dictionary
# It's needed to store the task(orchester) in the Experiment DB model.
session_info = {}

@app.get("/")
async def get_state():
    return {"state":"online"}

@app.post("/dataset/upload/")
async def upload_dataset(file: UploadFile = File(...)):
    """
    Creates an experiment with the information in file, the dataset and the task.
    It also stores the task object in a dictionary.
    """
    # Get Dataset from File
    try:
        dataset = json.load(file.file)
    except:
        return {"message": "Couldn't read file."}
    finally:
        file.file.close()
    
    task_name = dataset["task_info"]["task_type"]

    experiment_id = None
    # Store experiment in DB
    try:
        experiment = models.Experiment(task_name, dataset)
        db.session.add(experiment)
        db.session.commit()
        experiment_id = experiment.id
        
    except:
        return {"message": "Couldn't connect with DB."}
    
    # Store task object in memory
    session_info[experiment_id] = { "task": Task.createTask(task_name) }

    return (experiment_id, get_model_params_from_task(task_name))

@app.post("/dataset/upload/{dataset_id}")
async def upload_dataset(dataset_id: int):
    return {"message": "To be implemented"}

@app.get("/dataset/task_name/{session_id}")
async def get_task_name(session_id: int):
    """
    Returns the task_name associated with the experiment of id session_id.
    """
    experiment : models.Experiment = db.session.query(models.Experiment).get(session_id)
    return experiment.task_name

@app.post("/selectedParameters/{model_name}")
async def execute_model(session_id : int, model_name : str, payload: dict = Body(...)):
    """
    Add the model to the experiment, with the parameters in the payload dictionary.
    The model will be saved in the DB.
    """
    main_task = session_info[session_id]["task"]
    main_task.set_executions(model_name, payload)
    # TODO save the execution in the DB
    # TODO do not store the model in the task, just keep track oh the id.
    # TODO save the models using a file (ex. .pickle) besides storing all the bytes.
    # To do that it's necesary to know where to store the models.
    execution_id = db.session.query(models.Execution).count() + len(main_task.executions)
    return execution_id
    
@app.post("/experiment/run/{session_id}")
async def run_experiment(session_id: int):
    """
    Execute the experiment, performing all the required training and after that computing the metrics.
    """
    experiment : models.Experiment = db.session.query(models.Experiment).get(session_id)
    main_task = session_info[session_id]["task"]
    main_task.run_experiments(experiment.dataset)

    # Store results in DB
    for exec_results in main_task.experimentResults.keys():
        execution = models.Execution(
            parameters=main_task.experimentResults[exec_results]["parameters"],
            train_results=main_task.experimentResults[exec_results]["train_results"],
            test_results=main_task.experimentResults[exec_results]["test_results"],
            exec_bytes=main_task.experimentResults[exec_results]["execution_bytes"],
        )
        db.session.add(execution)
    db.session.commit()

    return session_id

@app.get("/experiment/results/{session_id}")
async def get_results(session_id: int):
    """
    Returns the results of the experiment in JSON format.
    """
    main_task = session_info[session_id]["task"]
    output = main_task.experimentResults
    # TODO get only the metrics
    for exec_name in output.keys():
        output[exec_name].pop("parameters")
        output[exec_name].pop("execution_bytes")
    return output

@app.get("/play/{session_id}/{execution_id}/{input}")
async def generate_prediction(session_id: int, execution_id: int, input_data: str):
    """
    Use the selected execution of the selected experiment to predict the output of a 
    given input.
    """
    main_task = session_info[session_id]["task"]
    return str(main_task.get_prediction(execution_id, input_data))

# CHECK USE
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
def select_model(model_name : str): 
    # TODO: Generalize this function to any kind of config object
    """
    It returns the squema of the selected model
    """
    try:
        return ConfigObject().get_squema(SquemaTypes.model, model_name)
    except:
        return f"Squema for {model_name} not found"

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

if __name__ == "__main__":
    # Init DB
    db.Base.metadata.create_all(db.engine)
    os.chdir("back") # Without this line, it is executed from DashAI folder
    uvicorn.run(app, host="127.0.0.1", port=8000)