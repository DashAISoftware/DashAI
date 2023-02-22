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

<<<<<<< HEAD
=======
session_info = {}
# main_task: Task

init_classes = {"CSVDataLoader": CSVDataLoader(), "JSONDataLoader": JSONDataLoader()}


def parse_params(params):
    """
    Parse JSON from string to pydantic model
    """
    try:
        model = DatasetParams.parse_raw(params)
        return model
    except pydantic.ValidationError as e:
        raise HTTPException(
            detail=jsonable_encoder(e.errors()),
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        ) from e


@app.get("/info")
async def get_state():
    return {"state": "online"}


@app.post("/dataset/upload/")
async def upload_dataset(
    params: str = Form(), url: str = Form(None), file: UploadFile = File(None)
):
    session_id = 0  # TODO: generate unique ids
    params = parse_params(params)
    dataloader = init_classes[params.data_loader]
    folder_path = f"../datasets/{params.dataset_name}"
    os.mkdir(folder_path)
    try:
        dataset = dataloader.load_data(
            dataset_path=folder_path,
            params=params.dataloader_params.dict(),
            file=file,
            url=url,
        )
        dataset, class_column = dataloader.set_classes(
            dataset, params.class_column
        )  # class_index -> class_column
        if not params.splits_in_folders:  # folder_split -> splits_in_folders
            dataset = dataloader.split_dataset(
                dataset, params.splits.dict(), class_column
            )
        dataset.save_to_disk(folder_path + "/dataset")

        # TODO: add dataset to register in DB

        session_info[session_id] = {
            "dataset": params.dataset_name,
            "task_name": params.task_name,
            # TODO Task throw exception if createTask fails
            "task": Task.createTask(params.task_name),
        }
        # TODO give session_id to user
        return get_model_params_from_task(params.task_name)
    except OSError:
        os.remove(folder_path)
        return {"message": "Couldn't read file."}


@app.get("/select/{schema_type}/{model_name}")
def select_schema(schema_type: str, model_name: str):
    """
    It returns the squema of any configurable object
    """
    try:
        return ConfigObject().get_squema(SquemaTypes[schema_type], model_name)
    except (FileNotFoundError, json.decoder.JSONDecodeError):
        return f"Squema for {model_name} not found"


@app.post("/dataset/upload/{dataset_id}")
async def upload_dataset_id(dataset_id: int):
    return {"message": dataset_id + " to be implemented in the future."}


@app.get("/dataset/task_name/{session_id}")  # It's not necessary anymore!
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
def select_model(model_name: str):
    # TODO: Generalize this function to any kind of config object
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

>>>>>>> JSON dataloader working

app.include_router(datasets.router)
app.include_router(experiments.router)


if __name__ == "__main__":
    db.Base.metadata.create_all(db.engine)
    # TODO: Check if db is running
    uvicorn.run(app, host="127.0.0.1", port=8000)
