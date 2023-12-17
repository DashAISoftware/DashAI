import json
import logging
import os
import pathlib
import shutil
from typing import Callable, Union

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, File, Form, Response, UploadFile, status
from fastapi.exceptions import HTTPException
from sqlalchemy import exc
from sqlalchemy.orm import Session
from typing_extensions import ContextManager

from DashAI.back.api.api_v1.schemas.datasets_params import DatasetParams
from DashAI.back.api.utils import parse_params
from DashAI.back.containers import Container
from DashAI.back.database.models import Dataset
from DashAI.back.dataloaders.classes.dashai_dataset import save_dataset
from DashAI.back.dataloaders.classes.dataloader import to_dashai_dataset
from DashAI.back.services.registry import ComponentRegistry

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
router = APIRouter()


@router.get("/")
@inject
async def get_datasets(
    session: Callable[..., ContextManager[Session]] = Depends(
        Provide[Container.db.provided.session]
    ),
):
    """Return every dataset stored in the database.

    Parameters
    ----------
    session : Callable[..., ContextManager[Session]], optional
        Sqlalchemy sesion maker wrapped in a context maker.

    Returns
    -------
    List[dict]
        Found datasets.
    """
    with session() as db:
        try:
            all_datasets = db.query(Dataset).all()

        except exc.SQLAlchemyError as e:
            logger.exception(e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal database error",
            ) from e

    return all_datasets


@router.get("/{dataset_id}")
@inject
async def get_dataset(
    dataset_id: int,
    session: Callable[..., ContextManager[Session]] = Depends(
        Provide[Container.db.provided.session]
    ),
):
    """Return an specific dataset.

    Parameters
    ----------
    dataset_id : int
        Id of the dataset to query.

    Returns
    -------
    Dict
        A Dict with the specified dataset id.
    """
    with session() as db:
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
    db: Session = Depends(Provide[Container.db]),
    params: str = Form(),
    url: str = Form(None),
    file: UploadFile = File(None),
    component_registry: ComponentRegistry = Depends(
        Provide[Container.component_registry]
    ),
    config=Depends(Provide[Container.config]),
):
    """Create a new dataset from a file or url.

    Parameters
    ----------
    session : Session, optional
        _description_, by default Depends(Provide[Container.db])
    params : str, optional
        Dataset configuration parameters.
    url : str, optional
        The url where the dataset is stored, by default Form(None).
    file : UploadFile, optional
        The file that contains the dataset, by default File(None).
    component_registry : ComponentRegistry
        The current app component registry provided by dependency injection.

    Returns
    -------
    Dataset
        The created dataset.
    """
    logger.debug("Uploading dataset.")
    logger.debug("Params: %s", str(params))

    parsed_params = parse_params(DatasetParams, params)
    dataloader = component_registry[parsed_params.dataloader]["class"]()
    folder_path = (
        pathlib.Path(config["DATASETS_PATH"]).expanduser() / parsed_params.dataset_name
    )

    try:
        logger.debug("Trying to create a new path: %s", folder_path)
        folder_path.mkdir(parents=True)
    except FileExistsError as e:
        logger.exception(e)
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A dataset with this name already exists",
        ) from e

    try:
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

        save_dataset(dataset, os.path.join(folder_path, "dataset"))

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

    with db.session() as db_session:
        try:
            folder_path = os.path.realpath(folder_path)
            dataset = Dataset(
                name=parsed_params.dataset_name,
                task_name=parsed_params.task_name,
                feature_names=json.dumps(inputs_columns),
                file_path=folder_path,
            )
            db_session.add(dataset)
            db_session.commit()
            db_session.refresh(dataset)
            return dataset

        except exc.SQLAlchemyError as e:
            logger.exception(e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal database error",
            ) from e


@router.delete("/{dataset_id}")
@inject
async def delete_dataset(
    dataset_id: int,
    session: Callable[..., ContextManager[Session]] = Depends(
        Provide[Container.db.provided.session]
    ),
):
    """Return the dataset with id dataset_id from the database.

    Parameters
    ----------
    dataset_id : int
        id of the dataset to delete.

    Returns
    -------
    Response with code 204 NO_CONTENT
    """
    with session() as db:
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
    session: Callable[..., ContextManager[Session]] = Depends(
        Provide[Container.db.provided.session]
    ),
    name: Union[str, None] = None,
    task_name: Union[str, None] = None,
):
    """Update an specific dataset name or task.

    Parameters
    ----------
    dataset_id : int
        id of the dataset to update.

    Returns
    -------
    Dict
        Dict containing the updated record
    """
    with session() as db:
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
