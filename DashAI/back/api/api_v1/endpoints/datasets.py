import json
import logging
import os
import shutil
from typing import Union

from fastapi import APIRouter, Depends, File, Form, Response, UploadFile, status
from fastapi.exceptions import HTTPException
from sqlalchemy import exc
from sqlalchemy.orm import Session

from DashAI.back.api.api_v1.schemas.datasets_params import DatasetParams
from DashAI.back.api.deps import get_db
from DashAI.back.api.utils import parse_params
from DashAI.back.core.config import component_registry, settings
from DashAI.back.database.models import Dataset
from DashAI.back.dataloaders.classes.dashai_dataset import save_dataset
from DashAI.back.dataloaders.classes.dataloader import to_dashai_dataset

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)

router = APIRouter()


@router.get("/")
async def get_datasets(db: Session = Depends(get_db)):
    """Return all the available datasets in the database.

    Returns
    -------
    List[dict]
        A list of dict containing datasets.
    """
    try:
        all_datasets = db.query(Dataset).all()

    except exc.SQLAlchemyError as e:
        log.exception(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal database error",
        ) from e

    return all_datasets


@router.get("/{dataset_id}")
async def get_dataset(dataset_id: int, db: Session = Depends(get_db)):
    """Return the dataset with id dataset_id from the database.

    Parameters
    ----------
    dataset_id : int
        id of the dataset to query.

    Returns
    -------
    JSON
        JSON with the specified dataset id.
    """
    try:
        dataset = db.get(Dataset, dataset_id)
        if not dataset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Dataset not found",
            )

    except exc.SQLAlchemyError as e:
        log.exception(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal database error",
        ) from e

    return dataset


@router.post("/", status_code=status.HTTP_201_CREATED)
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
    JSON
        JSON with the new dataset on the database
    """
    params = parse_params(DatasetParams, params)
    dataloader = component_registry[params.dataloader]["class"]()
    folder_path = os.path.join(settings.USER_DATASET_PATH, params.dataset_name)

    try:
        os.makedirs(folder_path)
    except FileExistsError as e:
        log.exception(e)
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A dataset with this name already exists",
        ) from e

    try:
        dataset = dataloader.load_data(
            dataset_path=folder_path,
            params=params.dataloader_params.dict(),
            file=file,
            url=url,
        )
        columns = dataset["train"].column_names
        outputs_columns = params.outputs_columns

        if len(outputs_columns) == 0:
            inputs_columns = columns[:-1]
            outputs_columns = [columns[-1]]
        else:
            inputs_columns = [x for x in columns if x not in outputs_columns]

        dataset = to_dashai_dataset(dataset, inputs_columns, outputs_columns)

        if not params.splits_in_folders:
            dataset = dataloader.split_dataset(
                dataset,
                params.splits.train_size,
                params.splits.test_size,
                params.splits.val_size,
                params.splits.seed,
                params.splits.shuffle,
                params.splits.stratify,
                outputs_columns[0],  # Stratify according
                # to the split is only done in classification,
                # so it will correspond to the class column.
            )

        save_dataset(dataset, os.path.join(folder_path, "dataset"))

        # - NOTE -------------------------------------------------------------
        # Is important that the DatasetDict dataset it be saved in "/dataset"
        # because for images and audio is also saved the original files,
        # So we have the original files and the "dataset" folder
        # with the DatasetDict that we use to handle the data.
        # --------------------------------------------------------------------

    except OSError as e:
        log.exception(e)
        shutil.rmtree(folder_path, ignore_errors=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to read file",
        ) from e

    try:
        folder_path = os.path.realpath(folder_path)
        dataset = Dataset(
            name=params.dataset_name,
            task_name=params.task_name,
            feature_names=json.dumps(inputs_columns),
            file_path=folder_path,
        )
        db.add(dataset)
        db.commit()
        db.refresh(dataset)
        return dataset

    except exc.SQLAlchemyError as e:
        log.exception(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal database error",
        ) from e


@router.delete("/{dataset_id}")
async def delete_dataset(dataset_id: int, db: Session = Depends(get_db)):
    """Return the dataset with id dataset_id from the database.

    Parameters
    ----------
    dataset_id : int
        id of the dataset to delete.

    Returns
    -------
    Response with code 204 NO_CONTENT
    """
    try:
        dataset = db.get(Dataset, dataset_id)
        if not dataset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Dataset not found",
            )

        db.delete(dataset)
        db.commit()

    except exc.SQLAlchemyError as e:
        log.exception(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal database error",
        ) from e

    try:
        shutil.rmtree(dataset.file_path, ignore_errors=True)
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    except OSError as e:
        log.exception(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete directory",
        ) from e


@router.patch("/{dataset_id}")
async def update_dataset(
    dataset_id: int,
    db: Session = Depends(get_db),
    name: Union[str, None] = None,
    task_name: Union[str, None] = None,
):
    """Update a dataset name or task.

    Parameters
    ----------
    dataset_id : int
        id of the dataset to update.

    Returns
    -------
    JSON
        JSON containing the updated record
    """
    try:
        dataset = db.get(Dataset, dataset_id)
        if name:
            setattr(dataset, "name", name)
        if task_name:
            setattr(dataset, "task_name", task_name)
        if name or task_name:
            db.commit()
            db.refresh(dataset)
            return dataset
        else:
            raise HTTPException(
                status_code=status.HTTP_304_NOT_MODIFIED,
                detail="Record not modified",
            )
    except exc.SQLAlchemyError as e:
        log.exception(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal database error",
        ) from e
