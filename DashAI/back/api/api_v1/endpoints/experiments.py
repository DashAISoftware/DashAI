import logging
from typing import Union

from fastapi import APIRouter, Depends, Response, status
from fastapi.exceptions import HTTPException
from kink import di, inject
from sqlalchemy import exc
from sqlalchemy.orm import sessionmaker

from DashAI.back.api.api_v1.schemas.experiments_params import (
    ColumnsValidationParams,
    ExperimentParams,
)
from DashAI.back.dataloaders.classes.dashai_dataset import (
    get_column_names_from_indexes,
    load_dataset,
)
from DashAI.back.dependencies.database.models import Dataset, Experiment
from DashAI.back.dependencies.registry import ComponentRegistry
from DashAI.back.tasks.base_task import BaseTask

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)

router = APIRouter()


@router.get("/")
@inject
async def get_experiments(
    session_factory: sessionmaker = Depends(lambda: di["session_factory"]),
):
    """Retrieve a list of the stored experiments in the database.

    Parameters
    ----------
    session_factory : Callable[..., ContextManager[Session]]
        A factory that creates a context manager that handles a SQLAlchemy session.
        The generated session can be used to access and query the database.


    Returns
    -------
    List[dict]
        A list of dict containing experiments.
    """
    with session_factory() as db:
        try:
            all_experiments = db.query(Experiment).all()
        except exc.SQLAlchemyError as e:
            log.exception(e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal database error",
            ) from e
        return all_experiments


@router.get("/{experiment_id}")
@inject
async def get_experiment(
    experiment_id: int,
    session_factory: sessionmaker = Depends(lambda: di["session_factory"]),
):
    """Retrieve the experiment associated with the provided ID.

    Parameters
    ----------
    experiment_id : int
        ID of the experiment to retrieve.
    session_factory : Callable[..., ContextManager[Session]]
        A factory that creates a context manager that handles a SQLAlchemy session.
        The generated session can be used to access and query the database.

    Returns
    -------
    JSON
        JSON with the specified experiment id.
    """
    with session_factory() as db:
        try:
            experiment = db.get(Experiment, experiment_id)
            if not experiment:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Experiment not found",
                )
        except exc.SQLAlchemyError as e:
            log.exception(e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal database error",
            ) from e
        return experiment


@router.post("/validation")
@inject
async def validate_columns(
    params: ColumnsValidationParams,
    component_registry: ComponentRegistry = Depends(lambda: di["component_registry"]),
    session_factory: sessionmaker = Depends(lambda: di["session_factory"]),
):
    with session_factory() as db:
        try:
            dataset = db.get(Dataset, params.dataset_id)
            if not dataset:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Dataset not found",
                )
            datasetdict = load_dataset(f"{dataset.file_path}/dataset")
            if not datasetdict:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Error while loading the dataset.",
                )
            inputs_names = get_column_names_from_indexes(
                datasetdict=datasetdict, indexes=params.inputs_columns
            )
            outputs_names = get_column_names_from_indexes(
                datasetdict=datasetdict, indexes=params.outputs_columns
            )

        except exc.SQLAlchemyError as e:
            log.exception(e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal database error",
            ) from e
    if params.task_name not in component_registry:
        raise HTTPException(
            status_code=404,
            detail=f"Task {params.task_name} not found in the registry.",
        )
    task: BaseTask = component_registry[params.task_name]["class"]()
    validation_response = {}
    try:
        prepared_dataset = task.prepare_for_task(
            datasetdict=datasetdict,
            outputs_columns=outputs_names,
        )
        task.validate_dataset_for_task(
            dataset=prepared_dataset,
            dataset_name=dataset.name,
            input_columns=inputs_names,
            output_columns=outputs_names,
        )
        validation_response["dataset_status"] = "valid"
    except (TypeError, ValueError) as e:
        validation_response["dataset_status"] = "invalid"
        validation_response["error"] = str(e)
    return validation_response


@router.post("/", status_code=status.HTTP_201_CREATED)
@inject
async def create_experiment(
    params: ExperimentParams,
    session_factory: sessionmaker = Depends(lambda: di["session_factory"]),
):
    """Create a new experiment.

    Parameters
    ----------
    params : ExperimentParams
        The new experiment parameters.
    session_factory : Callable[..., ContextManager[Session]]
        A factory that creates a context manager that handles a SQLAlchemy session.
        The generated session can be used to access and query the database.

    Returns
    -------
    Experiment
        The created experiment.

    Raises
    ------
    HTTPException
        If the dataset with id dataset_id is not registered in the DB.
    """
    with session_factory() as db:
        try:
            dataset = db.get(Dataset, params.dataset_id)
            if not dataset:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found"
                )
            datasetdict = load_dataset(f"{dataset.file_path}/dataset")
            if not datasetdict:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Error while loading the dataset.",
                )
            inputs_columns = get_column_names_from_indexes(
                datasetdict=datasetdict, indexes=params.input_columns
            )
            outputs_columns = get_column_names_from_indexes(
                datasetdict=datasetdict, indexes=params.output_columns
            )
            experiment = Experiment(
                dataset_id=params.dataset_id,
                task_name=params.task_name,
                name=params.name,
                input_columns=inputs_columns,
                output_columns=outputs_columns,
                splits=params.splits,
            )
            db.add(experiment)
            db.commit()
            db.refresh(experiment)
            return experiment
        except exc.SQLAlchemyError as e:
            log.exception(e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal database error",
            ) from e


@router.delete("/{experiment_id}")
@inject
async def delete_experiment(
    experiment_id: int,
    session_factory: sessionmaker = Depends(lambda: di["session_factory"]),
):
    """Delete the experiment associated with the provided ID from the database.

    Parameters
    ----------
    experiment_id : int
        ID of the experiment to be deleted.
    session_factory : Callable[..., ContextManager[Session]]
        A factory that creates a context manager that handles a SQLAlchemy session.
        The generated session can be used to access and query the database.

    Returns
    -------
    Response with code 204 NO_CONTENT
    """
    with session_factory() as db:
        try:
            experiment = db.get(Experiment, experiment_id)
            if not experiment:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Experiment not found",
                )
            db.delete(experiment)
            db.commit()
            return Response(status_code=status.HTTP_204_NO_CONTENT)
        except exc.SQLAlchemyError as e:
            log.exception(e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal database error",
            ) from e


@router.patch("/{experiment_id}")
@inject
async def update_dataset(
    experiment_id: int,
    dataset_id: Union[int, None] = None,
    task_name: Union[str, None] = None,
    name: Union[str, None] = None,
    session_factory: sessionmaker = Depends(lambda: di["session_factory"]),
):
    """Update the experiment associated with the provided ID.

    Parameters
    ----------
    experiment_id : int
        ID of the dataset to update.
    session_factory : Callable[..., ContextManager[Session]]
        A factory that creates a context manager that handles a SQLAlchemy session.
        The generated session can be used to access and query the database.

    Returns
    -------
    Dict
        A dictionary containing the updated experiment record.
    """
    with session_factory() as db:
        try:
            experiment = db.get(Experiment, experiment_id)
            if dataset_id:
                setattr(experiment, "dataset_id", dataset_id)
            if task_name:
                setattr(experiment, "task_name", task_name)
            if name:
                setattr(experiment, "name", name)
            if dataset_id or task_name or name:
                db.commit()
                db.refresh(experiment)
                return experiment
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
