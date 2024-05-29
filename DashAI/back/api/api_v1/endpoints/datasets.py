import logging
import os
import shutil
from typing import Any, Dict

from fastapi import APIRouter, Depends, File, Form, Response, UploadFile, status
from fastapi.exceptions import HTTPException
from kink import di, inject
from sqlalchemy import exc
from sqlalchemy.orm.session import sessionmaker

from DashAI.back.api.api_v1.schemas.datasets_params import (
    DatasetParams,
    DatasetUpdateParams,
)
from DashAI.back.api.utils import parse_params
from DashAI.back.dataloaders.classes.dashai_dataset import (
    DashAIDataset,
    get_columns_spec,
    get_dataset_info,
    load_dataset,
    save_dataset,
    split_dataset,
    split_indexes,
    to_dashai_dataset,
    update_columns_spec,
)
from DashAI.back.dependencies.database.models import Dataset
from DashAI.back.dependencies.registry import ComponentRegistry

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/")
@inject
async def get_datasets(
    session_factory: sessionmaker = Depends(lambda: di[sessionmaker]),
):
    """Retrieve a list of the stored datasets in the database.

    Parameters
    ----------
    session_factory : sessionmaker
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
    logger.debug("Retrieving all datasets.")
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
    session_factory: sessionmaker = Depends(lambda: di[sessionmaker]),
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
    logger.debug("Retrieving dataset with id %s", dataset_id)
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


@router.get("/{dataset_id}/sample")
@inject
async def get_sample(
    dataset_id: int,
    session_factory: sessionmaker = Depends(lambda: di[sessionmaker]),
):
    """Return the dataset with id dataset_id from the database.

    Parameters
    ----------
    dataset_id : int
        id of the dataset to query.

    Returns
    -------
    Dict
        A Dict with a sample of 10 rows
    """
    with session_factory() as db:
        try:
            file_path = db.get(Dataset, dataset_id).file_path
            if not file_path:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Dataset not found",
                )
            dataset: DashAIDataset = load_dataset(f"{file_path}/dataset")
            sample = dataset["train"].sample(n=10)
        except exc.SQLAlchemyError as e:
            logger.exception(e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal database error",
            ) from e
    return sample


@router.get("/{dataset_id}/info")
@inject
async def get_info(
    dataset_id: int,
    session_factory: sessionmaker = Depends(lambda: di[sessionmaker]),
):
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
    with session_factory() as db:
        try:
            dataset = db.get(Dataset, dataset_id)
            if not dataset:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Dataset not found",
                )
            info = get_dataset_info(f"{dataset.file_path}/dataset")
        except exc.SQLAlchemyError as e:
            logger.exception(e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal database error",
            ) from e
    return info


@router.get("/{dataset_id}/types")
@inject
async def get_types(
    dataset_id: int,
    session_factory: sessionmaker = Depends(lambda: di[sessionmaker]),
):
    """Return the dataset with id dataset_id from the database.

    Parameters
    ----------
    dataset_id : int
        id of the dataset to query.

    Returns
    -------
    Dict
        Dict containing column names and types.
    """
    with session_factory() as db:
        try:
            file_path = db.get(Dataset, dataset_id).file_path
            if not file_path:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Dataset not found",
                )
            columns_spec = get_columns_spec(f"{file_path}/dataset")
            if not columns_spec:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Error while loading column types.",
                )
        except exc.SQLAlchemyError as e:
            logger.exception(e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal database error",
            ) from e
    return columns_spec


@router.post("/", status_code=status.HTTP_201_CREATED)
@inject
async def upload_dataset(
    params: str = Form(),
    url: str = Form(None),
    file: UploadFile = File(None),
    component_registry: ComponentRegistry = Depends(lambda: di[ComponentRegistry]),
    session_factory: sessionmaker = Depends(lambda: di[sessionmaker]),
    config: Dict[str, Any] = Depends(lambda: di["config"]),
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
    logger.debug("Creating a new dataset.")
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
        logger.debug("Storing dataset in %s", folder_path)
        new_dataset = dataloader.load_data(
            filepath_or_buffer=file if file is not None else url,
            temp_path=str(folder_path),
            params=parsed_params.dataloader_params.dict(),
        )

        new_dataset = to_dashai_dataset(new_dataset)

        if not parsed_params.splits_in_folders:
            n = len(new_dataset["train"])
            train_indexes, test_indexes, val_indexes = split_indexes(
                n,
                parsed_params.splits.train_size,
                parsed_params.splits.test_size,
                parsed_params.splits.val_size,
                parsed_params.splits.seed,
                parsed_params.splits.shuffle,
            )
            new_dataset = split_dataset(
                new_dataset["train"],
                train_indexes=train_indexes,
                test_indexes=test_indexes,
                val_indexes=val_indexes,
            )
            dataset_path = folder_path / "dataset"
        logger.debug("Saving dataset in %s", str(dataset_path))
        save_dataset(new_dataset, dataset_path)

        # - NOTE -------------------------------------------------------------
        # Is important that the DatasetDict dataset it be saved in "/dataset"
        # because for images and audio is also saved the original files,
        # So we have the original files and the "dataset" folder
        # with the DatasetDict that we use to handle the data.
        # --------------------------------------------------------------------

    except OSError as e:
        shutil.rmtree(folder_path, ignore_errors=True)
        logger.exception(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to read file",
        ) from e

    with session_factory() as db:
        logger.debug("Storing dataset metadata in database.")
        try:
            folder_path = os.path.realpath(folder_path)
            new_dataset = Dataset(
                name=parsed_params.dataset_name,
                file_path=folder_path,
            )
            db.add(new_dataset)
            db.commit()

        except exc.SQLAlchemyError as e:
            logger.exception(e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal database error",
            ) from e

    logger.debug("Dataset creation sucessfully finished.")
    return new_dataset


@router.delete("/{dataset_id}")
@inject
async def delete_dataset(
    dataset_id: int,
    session_factory: sessionmaker = Depends(lambda: di[sessionmaker]),
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
    logger.debug("Deleting dataset with id %s", dataset_id)
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
    params: DatasetUpdateParams,
    session_factory: sessionmaker = Depends(lambda: di[sessionmaker]),
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
            if params.columns:
                update_columns_spec(f"{dataset.file_path}/dataset", params.columns)
            if params.name:
                setattr(dataset, "name", params.name)
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
