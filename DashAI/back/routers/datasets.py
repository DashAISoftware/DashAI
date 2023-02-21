import os

import pydantic
from Database import db, models

# from Dataloaders.classes.audioDataLoader import AudioDataLoader
# from Dataloaders.classes.csvDataLoader import CSVDataLoader
# from Dataloaders.classes.imageDataLoader import ImageDataLoader
from Dataloaders.dataLoadModel import DatasetParams
from fastapi import APIRouter, File, Form, UploadFile, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import HTTPException
from Models.classes.getters import get_model_params_from_task
from routers.session_class import session_info
from sqlalchemy import exc
from TaskLib.task.taskMain import Task

router = APIRouter()


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


@router.get("/dataset/")
async def get_dataset():
    """
    Returns all the available datasets in the DB.
    """

    available_datasets = {}

    for db_dataset in db.session.query(models.Dataset).order_by(models.Dataset.id):
        act_dataset = {
            "dataset_id": db_dataset.id,
            "dataset_name": db_dataset.name,
            "dataset_task_name": db_dataset.task_name,
            "dataset_path": db_dataset.path,
        }
        available_datasets[db_dataset.id] = act_dataset

    return available_datasets


# @router.post("/dataset/") TODO Change this route to this
@router.post("/dataset/upload/")
async def upload_dataset(
    params: str = Form(), url: str = Form(None), file: UploadFile = File(None)
):
    """
    Endpoint to Upload Datasets from user's input.
    Returns a list of available models for the dataset's task.
    """
    params = parse_params(params)
    # TODO Globals call is removed on the next iteration of dataloaders branch
    dataloader = globals()[params.data_loader]()
    folder_path = f"user_datasets/{params.dataset_name}"
    os.makedirs(folder_path)
    try:
        dataset = dataloader.load_data(
            dataset_path=folder_path,
            params=params.dataloader_params.dict(),
            file=file,
            url=url,
        )
        dataset, class_column = dataloader.set_classes(dataset, params.class_index)
        if not params.folder_split:
            dataset = dataloader.split_dataset(
                dataset, params.splits.dict(), class_column
            )
        dataset.save_to_disk(folder_path)
    except OSError:
        os.remove(folder_path)
        return {"message": "Couldn't read file."}
    try:
        folder_path = os.path.realpath(folder_path)
        db_dataset = models.Dataset(params.dataset_name, params.task_name, folder_path)
        db.session.add(db_dataset)
        db.session.flush()
        db.session.commit()

        # TODO remove this
        session_info.dataset = dataset
        session_info.task_name = params.task_name
        session_info.task = Task.createTask(params.task_name)

        return get_model_params_from_task(params.task_name)
    except exc.SQLAlchemyError:
        return {"message": "Couldn't connect with DB."}


@router.get("/dataset/task_name/{session_id}")
async def get_task_name():
    """
    Returns the task_name associated with the experiment of id session_id.
    """
    try:
        return session_info.task_name
    except AttributeError:
        return {"message": "There was a problem obtaining the dataset's task"}
