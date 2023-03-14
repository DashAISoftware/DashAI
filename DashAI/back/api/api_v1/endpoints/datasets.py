import logging
import os

import pydantic
from fastapi import APIRouter, File, Form, UploadFile, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import HTTPException
from sqlalchemy import exc

from DashAI.back.api.api_v0.endpoints.session_class import session_info
from DashAI.back.core.config import model_registry, settings
from DashAI.back.database import db, models
from DashAI.back.dataloaders.classes.csv_dataloader import CSVDataLoader

# from Dataloaders.classes.audioDataLoader import AudioDataLoader
# from Dataloaders.classes.csvDataLoader import CSVDataLoader
# from Dataloaders.classes.imageDataLoader import ImageDataLoader
from DashAI.back.dataloaders.classes.dataloader_params import DatasetParams
from DashAI.back.dataloaders.classes.json_dataloader import JSONDataLoader
from DashAI.back.tasks import (
    TabularClassificationTask,
    TextClassificationTask,
    TranslationTask,
)

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)

router = APIRouter()

dataloaders = {"CSVDataLoader": CSVDataLoader(), "JSONDataLoader": JSONDataLoader()}
tasks = {
    "TabularClassificationTask": TabularClassificationTask,
    "TextClassificationTask": TextClassificationTask,
    "TranslationTask": TranslationTask,
}


def parse_params(params):
    """
    Parse JSON from string to pydantic model

    Args:
        params (str): JSON with parameters for load the data in a string.

    Returns:
        BaseModel: Pydantic model parsed from JSON in parameters string.
    """
    try:
        model = DatasetParams.parse_raw(params)
        return model
    except pydantic.ValidationError as e:
        log.error(e)
        raise HTTPException(
            detail=jsonable_encoder(e.errors()),
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        ) from e


@router.get("/")
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
    except exc.SQLAlchemyError as e:
        log.error(e)
        return {"message": "Couldn't connect with DB."}
    return available_datasets


@router.post("/")
async def upload_dataset(
    params: str = Form(), url: str = Form(None), file: UploadFile = File(None)
):
    """
    Enpoint to upload datasets from user's input in a file or url.

    Args:
        params (str): Dataset parameters in JSON format inside a string.
        url (str, optional): For load the dataset from an URL.
            It's optional because is not necessary if the dataset is uploaded in a file.
        file (UploadFile, optional): File uploaded
            It's optional because is not necessary if the dataset is uploaded in a URL.

    Return:
        list[str]:  List of available models for the dataset's task.
    --------------------------------------------------------------------------------
    - NOTE: It's not possible to upload a JSON (Pydantic model or directly JSON)
            and files in the same endpoint. For that reason, the parameters are
            submited in a string that contains the parameters defined in the
            pydantic model 'DatasetParams', that you can find in the file
            'dataloaders/classes/dataloader_params.py'.
    ---------------------------------------------------------------------------------
    """
    params = parse_params(params)
    dataloader = dataloaders[params.dataloader]
    folder_path = f"{settings.USER_DATASET_PATH}/{params.dataset_name}"
    try:
        os.makedirs(folder_path)
    except FileExistsError as e:
        log.error(e)
        return {"message": "Dataset name already exists."}
    try:
        dataset = dataloader.load_data(
            dataset_path=folder_path,
            params=params.dataloader_params.dict(),
            file=file,
            url=url,
        )
        # TODO: Not sure this is ok.
        task = tasks[params.task_name].create()
        # validation = task.validate_dataset(dataset, params.class_column)
        # if validation is not None:  # TODO: Validation with exceptions
        #     os.remove(folder_path)
        #     return {"message": validation}
        # else
        dataset, class_column = dataloader.set_classes(dataset, params.class_column)
        if not params.splits_in_folders:
            dataset = dataloader.split_dataset(
                dataset,
                params.splits.train_size,
                params.splits.test_size,
                params.splits.val_size,
                params.splits.seed,
                params.splits.shuffle,
                params.splits.stratify,
                class_column,
            )
        dataset.save_to_disk(f"{folder_path}/dataset")
        # - NOTE -------------------------------------------------------------
        # Is important that the DatasetDict dataset it be saved in "/dataset"
        # because for images and audio is also saved the original files,
        # So we have the original files and the "dataset" folder
        # with the DatasetDict that we use to handle the data.
        # --------------------------------------------------------------------
    except OSError as e:
        log.error(e)
        os.remove(folder_path)
        return {"message": "Couldn't read file."}
    try:
        folder_path = os.path.realpath(folder_path)
        db_dataset = models.Dataset(
            name=params.dataset_name, task_name=params.task_name, file_path=folder_path
        )
        db.session.add(db_dataset)
        db.session.flush()
        db.session.commit()

        # TODO remove this, only compatibility with api/v0
        session_info.dataset = dataset
        session_info.task_name = params.task_name
        session_info.task = task
        return model_registry.task_to_components(params.task_name)
    except exc.SQLAlchemyError as e:
        log.error(e)
        return {"message": "Database error"}


@router.delete("/")
async def delete_dataset():
    raise NotImplementedError


@router.put("/")
async def update_dataset():
    raise NotImplementedError
