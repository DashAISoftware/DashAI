import logging
import os
import pickle
from typing import Callable

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, status
from fastapi.exceptions import HTTPException
from sqlalchemy import exc, select
from sqlalchemy.orm import Session
from typing_extensions import ContextManager

from DashAI.back.api.api_v1.schemas.explainers_params import (
    GlobalExplainerParams,
    LocalExplainerParams,
    ValidateInstanceParams,
)
from DashAI.back.containers import Container
from DashAI.back.core.enums.status import ExplainerStatus
from DashAI.back.dataloaders.classes.dashai_dataset import load_dataset
from DashAI.back.dependencies.database.models import (
    Dataset,
    Experiment,
    GlobalExplainer,
    LocalExplainer,
    Run,
)
from DashAI.back.dependencies.registry import ComponentRegistry
from DashAI.back.tasks import BaseTask

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)

router = APIRouter()


@router.get("/global")
@inject
async def get_global_explainers(
    run_id: int,
    session_factory: Callable[..., ContextManager[Session]] = Depends(
        Provide[Container.db.provided.session]
    ),
):
    """Returns the available global explanainers in the database associated with the
    run_id.

    Parameters
    ----------
    run_id: int
        Run id to select the global explanations to retrieve.
    session_factory : Callable[..., ContextManager[Session]]
        A factory that creates a context manager that handles a SQLAlchemy session.
        The generated session can be used to access and query the database.

    Returns
    -------
    List[dict]
        A list of dicts containing global explainers.

    Raises
    ------
    HTTPException
        If there are no global explainers associated with the run_id in the DB.
    """
    with session_factory() as db:
        try:
            global_explainers = db.scalars(
                select(GlobalExplainer).where(GlobalExplainer.run_id == run_id)
            ).all()

        except exc.SQLAlchemyError as e:
            log.exception(e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal database error",
            ) from e

    return global_explainers


@router.get("/global/explanation/{explainer_id}")
@inject
async def get_global_explanation(
    explainer_id: int,
    component_registry: ComponentRegistry = Depends(
        Provide[Container.component_registry]
    ),
    session_factory: Callable[..., ContextManager[Session]] = Depends(
        Provide[Container.db.provided.session]
    ),
):
    """Returns the global explanation associated with id explainer_id.

    Parameters
    ----------
    explaniner_id: int
        Id to select the global explanation to retrieve.
    session_factory : Callable[..., ContextManager[Session]]
        A factory that creates a context manager that handles a SQLAlchemy session.
        The generated session can be used to access and query the database.

    Returns
    -------
    List[dict]
        A JSON with the explanation.

    Raises
    ------
    HTTPException
        If there is no global explanation associated with the explanation_id in the
        database.
    """
    with session_factory() as db:
        try:
            global_explainer = db.scalars(
                select(GlobalExplainer).where(GlobalExplainer.id == explainer_id)
            ).all()

            if not global_explainer:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Explainer not found",
                )

            if global_explainer[0].status != ExplainerStatus.FINISHED:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Explaination not found",
                )

            explanation_path = global_explainer[0].explanation_path

            with open(explanation_path, "rb") as file:
                explanation = pickle.load(file)

        except exc.SQLAlchemyError as e:
            log.exception(e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal database error",
            ) from e

    return explanation


@router.get("/global/explanation/plot/{explainer_id}")
@inject
async def get_global_explanation_plot(
    explainer_id: int,
    component_registry: ComponentRegistry = Depends(
        Provide[Container.component_registry]
    ),
    session_factory: Callable[..., ContextManager[Session]] = Depends(
        Provide[Container.db.provided.session]
    ),
):
    """Returns the global explanation plot associated with id explainer_id.

    Parameters
    ----------
    explaniner_id: int
        Id to select the global explanation plot to retrieve.
    session_factory : Callable[..., ContextManager[Session]]
        A factory that creates a context manager that handles a SQLAlchemy session.
        The generated session can be used to access and query the database.

    Returns
    -------
    List[dict]
        A JSON with the explanation plot.

    Raises
    ------
    HTTPException
        If there is no global explanation associated with the explanation_id in the
        database.
    """
    with session_factory() as db:
        try:
            global_explainer = db.scalars(
                select(GlobalExplainer).where(GlobalExplainer.id == explainer_id)
            ).all()

            if not global_explainer:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Explainer not found",
                )

            if global_explainer[0].status != ExplainerStatus.FINISHED:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Explaination plot not found",
                )

            plot_path = global_explainer[0].plot_path

            with open(plot_path, "rb") as file:
                plot = pickle.load(file)

        except exc.SQLAlchemyError as e:
            log.exception(e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal database error",
            ) from e

    return plot


@router.post("/global", status_code=status.HTTP_201_CREATED)
@inject
async def upload_global_explainer(
    params: GlobalExplainerParams,
    session_factory: Callable[..., ContextManager[Session]] = Depends(
        Provide[Container.db.provided.session]
    ),
):
    """Endpoint to create a global explainer

    Parameters
    ----------
    name: string
        User's name for the explainer
    run_id: int
        Id of the run associated with the explainer
    explainer_name: str
        Selected explainer
    parameters: dict
        Explainer configuration parameters
    session_factory : Callable[..., ContextManager[Session]]
        A factory that creates a context manager that handles a SQLAlchemy session.
        The generated session can be used to access and query the database.

    Returns
    -------
    dict
        Dict with the new global explainer.

    Raises
    ------
    HTTPException
        If the explainer cannot be saved to the database.
    """
    with session_factory() as db:
        try:
            run: Run = db.get(Run, params.run_id)
            if not run:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="Run not found"
                )

            log.info(f"paramss: {params}")
            explanation = GlobalExplainer(
                name=params.name,
                run_id=params.run_id,
                explainer_name=params.explainer_name,
                parameters=params.parameters,
            )

            db.add(explanation)
            db.commit()
            db.refresh(explanation)

            return explanation

        except exc.SQLAlchemyError as e:
            log.exception(e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal database error",
            ) from e


@router.delete("/global/{explainer_id}")
@inject
async def delete_global_explainer(
    explainer_id: int,
    session_factory: Callable[..., ContextManager[Session]] = Depends(
        Provide[Container.db.provided.session]
    ),
):
    """Delete the global explainer with id explanation_id from the database and its
    associated explanation file.

    Parameters
    ----------
    explainer_id : int
        Id of the global explainer to delete.
    session_factory : Callable[..., ContextManager[Session]]
        A factory that creates a context manager that handles a SQLAlchemy session.
        The generated session can be used to access and query the database.

    Raises
    ------
    HTTPException
        If the global explanation with id explanation_id is not registered in the DB.
    """
    with session_factory() as db:
        try:
            global_explainer = db.get(GlobalExplainer, explainer_id)
            if not global_explainer:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Explainer not found",
                )

            if global_explainer.explanation_path is not None:
                os.remove(global_explainer.explanation_path)

            db.delete(global_explainer)
            db.commit()

        except exc.SQLAlchemyError as e:
            log.exception(e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal database error",
            ) from e


@router.get("/local")
@inject
async def get_local_explainers(
    run_id: int,
    session_factory: Callable[..., ContextManager[Session]] = Depends(
        Provide[Container.db.provided.session]
    ),
):
    """Returns the available local explanainers in the database associated with the
    run_id.

    Parameters
    ----------
    run_id: int
        Run id to select the global explanations to retrieve.
    session_factory : Callable[..., ContextManager[Session]]
        A factory that creates a context manager that handles a SQLAlchemy session.
        The generated session can be used to access and query the database.

    Returns
    -------
    List[dict]
        A list of dicts containing local explainers.

    Raises
    ------
    HTTPException
        If there are no local explainers associated with the run_id in the DB.
    """
    with session_factory() as db:
        try:
            local_explainers = db.scalars(
                select(LocalExplainer).where(LocalExplainer.run_id == run_id)
            ).all()

        except exc.SQLAlchemyError as e:
            log.exception(e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal database error",
            ) from e

    return local_explainers


@router.get("/local/explanation/{explainer_id}")
@inject
async def get_local_explanation(
    explainer_id: int,
    component_registry: ComponentRegistry = Depends(
        Provide[Container.component_registry]
    ),
    session_factory: Callable[..., ContextManager[Session]] = Depends(
        Provide[Container.db.provided.session]
    ),
):
    """Returns the local explanation associated with id explainer_id.

    Parameters
    ----------
    explaniner_id: int
        Id to select the local explanation to retrieve.
    session_factory : Callable[..., ContextManager[Session]]
        A factory that creates a context manager that handles a SQLAlchemy session.
        The generated session can be used to access and query the database.

    Returns
    -------
    List[dict]
        A JSON with the explanation.

    Raises
    ------
    HTTPException
        If there is no local explanation associated with the explanation_id in the
        database.
    """
    with session_factory() as db:
        try:
            local_explainer = db.scalars(
                select(LocalExplainer).where(LocalExplainer.id == explainer_id)
            ).all()

            if not local_explainer:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Explainer not found",
                )

            if local_explainer[0].status != ExplainerStatus.FINISHED:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Explanation not found",
                )

            explanation_path = local_explainer[0].explanation_path

            with open(explanation_path, "rb") as file:
                explanation = pickle.load(file)

        except exc.SQLAlchemyError as e:
            log.exception(e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal database error",
            ) from e

    return explanation


@router.get("/local/explanation/plot/{explainer_id}")
@inject
async def get_local_explanation_plot(
    explainer_id: int,
    component_registry: ComponentRegistry = Depends(
        Provide[Container.component_registry]
    ),
    session_factory: Callable[..., ContextManager[Session]] = Depends(
        Provide[Container.db.provided.session]
    ),
):
    """Returns the local explanation plot associated with id explainer_id.

    Parameters
    ----------
    explaniner_id: int
        Id to select the local explanation plot to retrieve.
    session_factory : Callable[..., ContextManager[Session]]
        A factory that creates a context manager that handles a SQLAlchemy session.
        The generated session can be used to access and query the database.

    Returns
    -------
    List[dict]
        A JSON with the explanation plot.

    Raises
    ------
    HTTPException
        If there is no local explanation associated with the explanation_id in the
        database.
    """
    with session_factory() as db:
        try:
            local_explainer = db.scalars(
                select(LocalExplainer).where(LocalExplainer.id == explainer_id)
            ).all()

            if not local_explainer:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Explainer not found",
                )

            if local_explainer[0].status != ExplainerStatus.FINISHED:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Explanation plot not found",
                )

            plot_path = local_explainer[0].plot_path

            with open(plot_path, "rb") as file:
                plot = pickle.load(file)

        except exc.SQLAlchemyError as e:
            log.exception(e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal database error",
            ) from e

    return plot


@router.post("/local", status_code=status.HTTP_201_CREATED)
@inject
async def upload_local_explainer(
    params: LocalExplainerParams,
    session_factory: Callable[..., ContextManager[Session]] = Depends(
        Provide[Container.db.provided.session]
    ),
):
    """Endpoint to create a local explainer

    Parameters
    ----------
    name: string
        User's name for the explainer
    run_id: int
        Id of the run associated with the explainer
    explainer_name: str
        Selected explainer
    dataset_id: int
        Id of the dataset with the instances to be explained.
    parameters: dict
        Explainer configuration parameters
    parameters: dict
        Explainer fit configuration parameters
    session_factory : Callable[..., ContextManager[Session]]
        A factory that creates a context manager that handles a SQLAlchemy session.
        The generated session can be used to access and query the database.

    Returns
    -------
    dict
        Dict with the new local explainer.

    Raises
    ------
    HTTPException
        If the explainer cannot be saved to the database.
    """
    with session_factory() as db:
        try:
            run: Run = db.get(Run, params.run_id)
            if not run:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="Run not found"
                )

            explanation = LocalExplainer(
                name=params.name,
                run_id=params.run_id,
                explainer_name=params.explainer_name,
                dataset_id=params.dataset_id,
                parameters=params.parameters,
                fit_parameters=params.fit_parameters,
            )

            db.add(explanation)
            db.commit()
            db.refresh(explanation)

            return explanation

        except exc.SQLAlchemyError as e:
            log.exception(e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal database error",
            ) from e


@router.delete("/local/{explainer_id}")
@inject
async def delete_local_explainer(
    explainer_id: int,
    session_factory: Callable[..., ContextManager[Session]] = Depends(
        Provide[Container.db.provided.session]
    ),
):
    """Deletes the local explainer with id explanation_id from the database and its
    associated explanation file.

    Parameters
    ----------
    explainer_id : int
        Id of the local explainer to delete.
    session_factory : Callable[..., ContextManager[Session]]
        A factory that creates a context manager that handles a SQLAlchemy session.
        The generated session can be used to access and query the database.

    Raises
    ------
    HTTPException
        If the local explanation with id explanation_id is not registered in the DB.
    """
    with session_factory() as db:
        try:
            local_explainer = db.get(LocalExplainer, explainer_id)
            if not local_explainer:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Explainer not found",
                )

            if local_explainer.explanation_path is not None:
                os.remove(local_explainer.explanation_path)

            db.delete(local_explainer)
            db.commit()

        except exc.SQLAlchemyError as e:
            log.exception(e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal database error",
            ) from e


@router.patch("/")
async def update_explainer() -> None:
    """Update explainer.

    Raises
    ------
    HTTPException
        Always raises exception as it was intentionally not implemented.
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Method not implemented"
    )


@router.post("/local/validate-instance")
@inject
async def validate_dataset(
    params: ValidateInstanceParams,
    component_registry=Provide["component_registry"],
    session_factory: Callable[..., ContextManager[Session]] = Depends(
        Provide[Container.db.provided.session]
    ),
):
    with session_factory() as db:
        try:
            run: Run = db.get(Run, params.run_id)
            if not run:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Run not found",
                )
            experiment: Experiment = db.get(Experiment, run.experiment_id)
            if not experiment:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Experiment not found",
                )

            dataset: Dataset = db.get(Dataset, params.dataset_id)
            if not dataset:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Dataset not found",
                )

            instances = load_dataset(f"{dataset.file_path}/dataset")
            if not instances:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Error while loading the dataset.",
                )

        except exc.SQLAlchemyError as e:
            log.exception(e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal database error",
            ) from e

    try:
        task: BaseTask = component_registry[experiment.task_name]["class"]()
    except Exception as e:
        log.exception(e)
        raise HTTPException(
            status_code=404,
            detail=f"Task {experiment.task_name} not found in the registry.",
        ) from e

    validation_response = {}
    input_columns = experiment.input_columns
    output_columns = experiment.output_columns
    try:
        # Validate dataset for task
        prepared_dataset = task.prepare_for_task(
            datasetdict=instances, outputs_columns=output_columns
        )
        task.validate_dataset_for_task(
            dataset=prepared_dataset,
            dataset_name=dataset.name,
            input_columns=input_columns,
            output_columns=output_columns,
        )

    except TypeError as e:
        validation_response["dataset_status"] = "invalid"
        validation_response["error"] = str(e)

    # Validate columns
    columns = input_columns + output_columns
    instances_columns = list(instances["train"].features)
    is_valid = set(columns).issubset(instances_columns)

    if not is_valid:
        validation_response["dataset_status"] = "invalid"
        validation_response["error"] = "Invalid columns"
        raise ValueError("Invalid dataset columns")

    else:
        validation_response["dataset_status"] = "valid"

    return validation_response
