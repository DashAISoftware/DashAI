import os

import pydantic
from fastapi import APIRouter, File, Form, UploadFile, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import HTTPException
from sqlalchemy import exc

from DashAI.back.database import db, models
from DashAI.back.dataloaders.classes.csv_dataloader import CSVDataLoader

# from Dataloaders.classes.audioDataLoader import AudioDataLoader
# from Dataloaders.classes.csvDataLoader import CSVDataLoader
# from Dataloaders.classes.imageDataLoader import ImageDataLoader
from DashAI.back.dataloaders.classes.dataloader_params import DatasetParams
from DashAI.back.models.classes.getters import get_model_params_from_task
from DashAI.back.routers.session_class import session_info
from DashAI.back.tasks.task import Task

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
    try:
        for db_dataset in db.session.query(models.Dataset):
            available_datasets[db_dataset.id] = {
                "dataset_name": db_dataset.name,
                "dataset_task_name": db_dataset.task_name,
                "dataset_path": db_dataset.path,
            }
    except exc.SQLAlchemyError:
        return {"message": "Couldn't connect with DB."}
    return available_datasets


@router.post("/dataset/")
async def upload_dataset(
    params: str = Form(), url: str = Form(None), file: UploadFile = File(None)
):
    """
    Endpoint to Upload Datasets from user's input.
    Returns a list of available models for the dataset's task.
    """
    params = parse_params(params)
    # TODO Multiple dataloaders, first ideas contain a dict with the structure:
    # {"CSVDataLoader": CSVDataLoader(), "JSONDataLoader": JSONDataLoader(), ...}
    dataloader = CSVDataLoader()
    folder_path = f"DashAI/back/user_datasets/{params.dataset_name}"
    try:
        os.makedirs(folder_path)
    except FileExistsError:
        return {"message": "Dataset name already exists."}
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


@router.delete("/dataset/")
async def delete_dataset():
    return {"message": "To be implemented"}


@router.put("/dataset/")
async def insert_dataset():
    return {"message": "To be implemented"}
