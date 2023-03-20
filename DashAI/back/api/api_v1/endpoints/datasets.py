import logging
import os
import shutil
from typing import Union

import pydantic
from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import HTTPException
from sqlalchemy import exc
from sqlalchemy.orm import Session

from DashAI.back.api.deps import get_db
from DashAI.back.core.config import model_registry, settings
from DashAI.back.database.models import Dataset
from DashAI.back.dataloaders.classes.csv_dataloader import CSVDataLoader

# from Dataloaders.classes.audioDataLoader import AudioDataLoader
# from Dataloaders.classes.csvDataLoader import CSVDataLoader
# from Dataloaders.classes.imageDataLoader import ImageDataLoader
from DashAI.back.dataloaders.classes.dataloader_params import DatasetParams
from DashAI.back.dataloaders.classes.json_dataloader import JSONDataLoader

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)

router = APIRouter()

# TODO: Do this in a better way, this was the fastest fix to get str -> class
# Maybe each class should have its respective representative string as variable

dataloaders = {"CSVDataLoader": CSVDataLoader(), "JSONDataLoader": JSONDataLoader()}


def parse_params(params):
    """
    Parse JSON from string to pydantic model

    Parameters
    ----------
    params : str
        JSON with parameters for load the data in a string.

    Returns
    -------
    BaseModel
        Pydantic model parsed from JSON in parameters string.

    Raises
    ------
    ValidationError
        If params can't be validated by the pydantic model
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
async def get_datasets(db: Session = Depends(get_db)):
    """
    Returns all the available datasets in the database.

    Returns
    -------
    List[Dict]
        List of datasets

    Raises
    ------
    SQLAlchemyError
        If the database connection or query fails.
    """

    try:
        all_datasets = db.query(Dataset).all()
        if not all_datasets:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="No datasets found"
            )
    except exc.SQLAlchemyError as e:
        log.error(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal database error",
        )
    return all_datasets


@router.get("/{dataset_id}")
async def get_dataset(dataset_id: int, db: Session = Depends(get_db)):
    """
    Returns the dataset with id dataset_id from the database.

    Parameters
    ----------
    dataset_id : int
        id of the dataset to query.

    Returns
    -------
    Dict
        Dataset dict with the specified id.

    Raises
    ------
    SQLAlchemyError
        If the database connection or query fails.
    """
    try:
        dataset = db.get(Dataset, dataset_id)
        if not dataset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found"
            )
    except exc.SQLAlchemyError as e:
        log.error(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal database error",
        )
    return dataset


@router.post("/")
async def upload_dataset(
    db: Session = Depends(get_db),
    params: str = Form(),
    url: str = Form(None),
    file: UploadFile = File(None),
):
    """
    Endpoint to upload datasets from user's input file or url.

    --------------------------------------------------------------------------------
    - NOTE: It's not possible to upload a JSON (Pydantic model or directly JSON)
            and files in the same endpoint. For that reason, the parameters are
            submited in a string that contains the parameters defined in the
            pydantic model 'DatasetParams', that you can find in the file
            'dataloaders/classes/dataloader_params.py'.
    ---------------------------------------------------------------------------------

    Parameters
    ----------
    params : str
        Dataset parameters in JSON format inside a string.
    url : str, optional
        For load the dataset from an URL.
    file : UploadFile, optional
        File uploaded

    Returns
    -------
    List[str]
        List of available models for the dataset's task.

    Raises
    ------
    SQLAlchemyError
        If the database connection or query fails.

    FileExistsError
        If the file already exists
    """
    params = parse_params(params)
    dataloader = dataloaders[params.dataloader]
    folder_path = f"{settings.USER_DATASET_PATH}/{params.dataset_name}"
    try:
        os.makedirs(folder_path)
    except FileExistsError as e:
        log.error(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="A dataset with this name already exists",
        )
    try:
        dataset = dataloader.load_data(
            dataset_path=folder_path,
            params=params.dataloader_params.dict(),
            file=file,
            url=url,
        )
        # TODO: Not sure this goes here.
        # task = task_registry[params.task_name].create()
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
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to read file",
        )
    try:
        folder_path = os.path.realpath(folder_path)
        dataset = Dataset(
            name=params.dataset_name, task_name=params.task_name, file_path=folder_path
        )
        db.add(dataset)
        db.commit()
        return model_registry.task_to_components(params.task_name)
    except exc.SQLAlchemyError as e:
        log.error(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal database error",
        )


@router.delete("/{dataset_id}")
async def delete_dataset(dataset_id: int, db: Session = Depends(get_db)):
    """
    Returns the dataset with id dataset_id from the database.

    Parameters
    ----------
    dataset_id : int
        id of the dataset to delete.

    Returns
    -------
    Dict
        "ok" : True if the operation was successful

    Raises
    ------
    SQLAlchemyError
        If the database connection or query fails.
    """
    try:
        dataset = db.get(Dataset, dataset_id)
        if not dataset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found"
            )
        db.delete(dataset)
        shutil.rmtree(dataset.file_path, ignore_errors=True)
        db.commit()
        return {"ok": True}
    except (exc.SQLAlchemyError, OSError) as e:
        log.error(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal database error",
        )


@router.put("/{dataset_id}")
async def update_dataset(
    dataset_id: int,
    db: Session = Depends(get_db),
    name: Union[str, None] = None,
    task_name: Union[str, None] = None,
):
    """
    Updates the dataset information with id dataset_id from the database.

    Parameters
    ----------
    dataset_id : int
        id of the dataset to delete.

    Returns
    -------
    Dict
        "ok" : True if the operation was successful

    Raises
    ------
    SQLAlchemyError
        If the database connection or query fails.
    """
    try:
        dataset = db.get(Dataset, dataset_id)
        if name:
            setattr(dataset, "name", name)
        if task_name:
            setattr(dataset, "task_name", task_name)
        if name or task_name:
            db.commit()
            return {"ok": True}
        else:
            raise HTTPException(
                status_code=status.HTTP_304_NOT_MODIFIED, detail="Record not modified"
            )
    except exc.SQLAlchemyError as e:
        log.error(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal database error",
        )
