import json
import logging
import os
import pathlib
import shutil
from typing import Any, Callable, Dict, Union

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, File, Form, Response, UploadFile, status
from fastapi.exceptions import HTTPException
from sqlalchemy import exc
from sqlalchemy.orm import Session
from typing_extensions import ContextManager

from DashAI.back.api.api_v1.schemas.datasets_params import DatasetParams
from DashAI.back.api.utils import parse_params
from DashAI.back.containers import Container
from DashAI.back.dataloaders.classes.dashai_dataset import save_dataset
from DashAI.back.dataloaders.classes.dataloader import to_dashai_dataset
from DashAI.back.dependencies.database.models import Dataset
from DashAI.back.dependencies.registry import ComponentRegistry

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
router = APIRouter()


@router.get("/")
@inject
async def get_datasets(
    session_factory: Callable[..., ContextManager[Session]] = Depends(
        Provide[Container.db.provided.session]
    ),
):
    """Retrieve a list of the stored datasets in the database.

    Parameters
    ----------
    session_factory : Callable[..., ContextManager[Session]]
        A factory that creates a context manager that handles a SQLAlchemy session.
        The generated session can be used to access and query the database.

    Returns
    -------
    List[dict]
        A list of dictionaries representing the found datasets.
        Each dictionary contains information about the dataset, including its name,
        type, description, and creation date.
        If no datasets are found, an empty list will be returned.
    """
    with session_factory() as db:
        try:
            datasets = db.query(Dataset).all()

        except exc.SQLAlchemyError as e:
            logger.exception(e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal database error",
            ) from e

    return datasets


@router.get("/{dataset_id}")
@inject
async def get_dataset(
    dataset_id: int,
    session_factory: Callable[..., ContextManager[Session]] = Depends(
        Provide[Container.db.provided.session]
    ),
):
    """Retrieve the dataset associated with the provided ID.

    Parameters
    ----------
    dataset_id : int
        ID of the dataset to retrieve.
    session_factory : Callable[..., ContextManager[Session]]
        A factory that creates a context manager that handles a SQLAlchemy session.
        The generated session can be used to access and query the database.

    Returns
    -------
    Dict
        A Dict containing the requested dataset details.
    """
    with session_factory() as db:
        try:
            dataset = db.get(Dataset, dataset_id)
            if not dataset:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Dataset not found",
                )

        except exc.SQLAlchemyError as e:
            logger.exception(e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal database error",
            ) from e

    return dataset


@router.post("/", status_code=status.HTTP_201_CREATED)
@inject
async def upload_dataset(
    params: str = Form(),
    url: str = Form(None),
    file: UploadFile = File(None),
    component_registry: ComponentRegistry = Depends(
        Provide[Container.component_registry]
    ),
    session_factory: Callable[..., ContextManager[Session]] = Depends(
        Provide[Container.db.provided.session]
    ),
    config: Dict[str, Any] = Depends(Provide[Container.config]),
):
    """Create a new dataset from a file or url.

    Parameters
    ----------
    params : str, optional
        A Dict containing configuration options for the new dataset.
    url : str, optional
        URL of the dataset file, mutually exclusive with uploading a file, by default
        Form(None).
    file : UploadFile, optional
        File object containing the dataset data, mutually exclusive with
        providing a URL, by default File(None).
    component_registry : ComponentRegistry
        Registry containing the current app available components.
    session_factory : Callable[..., ContextManager[Session]]
        A factory that creates a context manager that handles a SQLAlchemy session.
        The generated session can be used to access and query the database.
    config: Dict[str, Any]
        Application settings.

    Returns
    -------
    Dataset
        The created dataset.
    """
    logger.debug("Uploading dataset.")
    logger.debug("Params: %s", str(params))

    parsed_params = parse_params(DatasetParams, params)
    dataloader = component_registry[parsed_params.dataloader]["class"]()
    folder_path = config["DATASETS_PATH"] / parsed_params.dataset_name

    # create dataset path
    try:
        logger.debug("Trying to create a new dataset path: %s", folder_path)
        folder_path.mkdir(parents=True)
    except FileExistsError as e:
        logger.exception(e)
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A dataset with this name already exists",
        ) from e

    # save dataset
    try:
        logging.debug("Storing dataset in %s", folder_path)
        dataset = dataloader.load_data(
            filepath_or_buffer=file if file is not None else url,
            temp_path=str(folder_path),
            params=parsed_params.dataloader_params.dict(),
        )
        columns = dataset["train"].column_names
        outputs_columns = parsed_params.outputs_columns

        if len(outputs_columns) == 0:
            outputs_columns = [s for s in columns if s in ["class", "label"]]
            if not outputs_columns:
                outputs_columns = [columns[-1]]

        inputs_columns = [x for x in columns if x not in outputs_columns]

        dataset = to_dashai_dataset(dataset, inputs_columns, outputs_columns)

        if not parsed_params.splits_in_folders:
            dataset = dataloader.split_dataset(
                dataset,
                parsed_params.splits.train_size,
                parsed_params.splits.test_size,
                parsed_params.splits.val_size,
                parsed_params.splits.seed,
                parsed_params.splits.shuffle,
                parsed_params.splits.stratify,
                outputs_columns[0],  # Stratify according
                # to the split is only done in classification,
                # so it will correspond to the class column.
            )

        save_dataset(dataset, folder_path / "dataset")

        # - NOTE -------------------------------------------------------------
        # Is important that the DatasetDict dataset it be saved in "/dataset"
        # because for images and audio is also saved the original files,
        # So we have the original files and the "dataset" folder
        # with the DatasetDict that we use to handle the data.
        # --------------------------------------------------------------------

    except OSError as e:
        logger.exception(e)
        shutil.rmtree(folder_path, ignore_errors=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to read file",
        ) from e

    with session_factory() as db:
        logging.debug("Storing dataset metadata in database.")
        try:
            folder_path = os.path.realpath(folder_path)
            dataset = Dataset(
                name=parsed_params.dataset_name,
                task_name=parsed_params.task_name,
                feature_names=json.dumps(inputs_columns),
                file_path=folder_path,
            )
            db.add(dataset)
            db.commit()
            db.refresh(dataset)

        except exc.SQLAlchemyError as e:
            logger.exception(e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal database error",
            ) from e

    logging.debug("Dataset stored sucessfully.")
    return dataset


@router.delete("/{dataset_id}")
@inject
async def delete_dataset(
    dataset_id: int,
    session_factory: Callable[..., ContextManager[Session]] = Depends(
        Provide[Container.db.provided.session]
    ),
):
    """Delete the dataset associated with the provided ID from the database.

    Parameters
    ----------
    dataset_id : int
        ID of the dataset to be deleted.
    session_factory : Callable[..., ContextManager[Session]]
        A factory that creates a context manager that handles a SQLAlchemy session.
        The generated session can be used to access and query the database.

    Returns
    -------
    Response with code 204 NO_CONTENT
    """
    with session_factory() as db:
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
            logger.exception(e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal database error",
            ) from e

    try:
        shutil.rmtree(dataset.file_path, ignore_errors=True)
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    except OSError as e:
        logger.exception(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete directory",
        ) from e


@router.patch("/{dataset_id}")
@inject
async def update_dataset(
    dataset_id: int,
    name: Union[str, None] = None,
    task_name: Union[str, None] = None,
    session_factory: Callable[..., ContextManager[Session]] = Depends(
        Provide[Container.db.provided.session]
    ),
):
    """Updates the name and/or task name of a dataset with the provided ID.

    Parameters
    ----------
    dataset_id : int
        ID of the dataset to update.
    name : str, optional
        New name for the dataset.
    task_name : str, optional
        New task name for the dataset.
    session_factory : Callable[..., ContextManager[Session]]
        A factory that creates a context manager that handles a SQLAlchemy session.
        The generated session can be used to access and query the database.

    Returns
    -------
    Dict
        A dictionary containing the updated dataset record.
    """
    with session_factory() as db:
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
            logger.exception(e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal database error",
            ) from e
