import json
import os
import pathlib

import uvicorn
from configObject import ConfigObject
from fastapi import Body, FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from Models.classes.getters import filter_by_parent, get_model_params_from_task

# TODO see how to avoid importing this
from Models.classes.sklearnLikeModel import SklearnLikeModel
from Models.enums.squema_types import SquemaTypes

# TODO These imports should be removed because they are unused, but currently needed.
from TaskLib.task.numericClassificationTask import NumericClassificationTask
from TaskLib.task.taskMain import Task
from TaskLib.task.textClassificationTask import TextClassificationTask
from TaskLib.task.TranslationTask import TranslationTask
from Database import db

from routers import datasets

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

@app.get("/info")
async def get_state():
    return {"state": "online"}

@app.post("/experiment/create/{dataset_id}")
async def experiment_create(dataset_id: int):
    """
    Creates an experiment with the dataset.
    It also stores the task object in the DB.
    """

    # load dataset from DB
    db_dataset: models.Dataset = db.session.query(models.Dataset).get(dataset_id)
    ds_path = db_dataset.path

    # Get Dataset from File
    try:
        f = open(ds_path, "r")
        dataset = json.load(f)
        f.close()
    except (IOError, json.decoder.JSONDecodeError):
        return {"message": "Couldn't read file."}

    task_name = dataset["task_info"]["task_type"]
    main_task = Task.createTask(task_name)

    experiment_id = None
    # Store experiment in DB
    try:
        experiment = models.Experiment(dataset)
        db.session.add(experiment)
        db.session.flush()
        experiment_id = experiment.id
        task_filepath = f"{task_folder}{main_task.NAME}_{experiment_id}{task_format}"
        main_task.save(task_filepath)
        experiment.task_filepath = task_filepath
        db.session.commit()

    except exc.SQLAlchemyError:
        return {"message": "Couldn't connect with DB."}

    return (experiment_id, get_model_params_from_task(task_name))

# @app.post("/selectedParameters/{model_name}")
# async def execute_model(session_id: int, model_name: str, payload: dict = Body(...)):
#     """
#     Add the model to the experiment, with the parameters in the payload dictionary.
#     The model will be saved in the DB.
#     """
#     experiment: models.Experiment = db.session.query(models.Experiment).get(session_id)
#     main_task = Task.load(experiment.task_filepath)
#     execution = main_task.set_executions(model_name, payload)

#     # Store execution in DB
#     execution_db = models.Execution(
#         experiment_id=session_id, parameters=execution.get_params()
#     )
#     db.session.add(execution_db)
#     db.session.flush()
#     execution_filepath = (
#         f"{execution_folder}{execution.MODEL}_{execution_db.id}{execution_format}"
#     )
#     execution.save(execution_filepath)
#     execution_db.exec_filepath = execution_filepath

#     main_task.executions_id.append(execution_db.id)
#     main_task.save(experiment.task_filepath)
#     db.session.commit()

#     return execution_db.id


# @app.post("/experiment/run/{session_id}")
# async def run_experiment(session_id: int):
#     """
#     Execute the experiment, performing all the required training and
#     after that computing the metrics.
#     """
#     experiment: models.Experiment = db.session.query(models.Experiment).get(session_id)
#     main_task = Task.load(experiment.task_filepath)

#     # Load models
#     for exec_id in main_task.executions_id:
#         execution_db: models.Execution = db.session.query(models.Execution).get(exec_id)
#         # TODO see how to load the model from Model
#         main_task.executions.append(SklearnLikeModel.load(execution_db.exec_filepath))

#     experimentResults = main_task.run_experiments(experiment.dataset)

#     # Store results in DB
#     for idx in range(len(main_task.executions)):
#         execution_db: models.Execution = db.session.query(models.Execution).get(
#             main_task.executions_id[idx]
#         )
#         exec_model_name = main_task.executions[idx].MODEL
#         main_task.executions[idx].save(execution_db.exec_filepath)
#         execution_db.train_results = experimentResults[exec_model_name]["train"]
#         execution_db.test_results = experimentResults[exec_model_name]["test"]
#         db.session.flush()

#     main_task.executions = []
#     main_task.save(experiment.task_filepath)
#     db.session.commit()

#     return session_id


# @app.get("/experiment/results/{session_id}")
# async def get_results(session_id: int):
#     """
#     Returns the results of the experiment in JSON format.
#     """
#     experiment: models.Experiment = db.session.query(models.Experiment).get(session_id)
#     return experiment.get_results()


@app.get("/play/{session_id}/{execution_id}/{input}")
async def generate_prediction(session_id: int, execution_id: int, input_data: str):
    """
    Use the selected execution of the selected experiment to predict the output of a
    given input.
    """
    experiment: models.Experiment = db.session.query(models.Experiment).get(session_id)
    main_task = Task.load(experiment.task_filepath)

    execution_db: models.Execution = db.session.query(models.Execution).get(
        execution_id
    )
    execution = SklearnLikeModel.load(execution_db.exec_filepath)

    return str(main_task.get_prediction(execution, input_data))


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


if __name__ == "__main__":
    db.Base.metadata.create_all(db.engine)
    uvicorn.run(app, host="127.0.0.1", port=8000)
