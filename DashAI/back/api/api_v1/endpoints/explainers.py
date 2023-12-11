import logging
import os
from typing import Union

from fastapi import APIRouter, Depends, status
from fastapi.exceptions import HTTPException
from sqlalchemy import exc, select
from sqlalchemy.orm import Session

from DashAI.back.api.api_v1.schemas.explainer_params import ExplainerParams
from DashAI.back.api.deps import get_db
from DashAI.back.core.config import component_registry, settings
from DashAI.back.database.models import Dataset, Experiment, Explainer, Run
from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset, load_dataset

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)

router = APIRouter()


@router.get("/")
async def get_explainers(
    run_id: Union[int, None] = None, db: Session = Depends(get_db)
):
    """Return the available explainers in the database.
    The explainers can be filtered by run_id.

    Parameters
    ----------
    run_id: Union[int, None], optional
        If specified, the function will return all the explainers associated with
        the run, by default None.

    Returns
    -------
    List[dict]
        A list of dict containing explainers.

    Raises
    ------
    HTTPException
        If explainer does not exist in the DB.
    """
    try:
        if run_id is not None:
            explainers = db.scalars(
                select(Explainer).where(Explainer.run_id == run_id)
            ).all()
            if not explainers:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Explainer associated with Run not found",
                )
        else:
            explainers = db.query(Explainer).all()

    except exc.SQLAlchemyError as e:
        log.exception(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal database error",
        ) from e

    return explainers


@router.get("/{explainer_id}")
async def get_explainer(explainer_id: int, db: Session = Depends(get_db)):
    """Return the explainer with id explainer_id from the database.

    Parameters
    ----------
    explainer_id : int
        id of the explainer to query.

    Returns
    -------
    dict
        Dict with the specified explainer id.

    Raises
    ------
    HTTPException
        If the explainer with id explainer_id is not registered in the DB.
    """
    try:
        explainer = db.get(Explainer, explainer_id)
        if not explainer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Explainer not found",
            )

    except exc.SQLAlchemyError as e:
        log.exception(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal database error",
        ) from e

    return explainer


@router.post("/", status_code=status.HTTP_201_CREATED)
async def upload_explainer(
    params: ExplainerParams,
    db: Session = Depends(get_db),
):
    """Endpoint to create an explainer

    Parameters
    ----------
    run_id: int
        Id of the run associated with the explainer
    explainer_name: str
        Name of the explainer
    parameters: dict
        Explainer configuration parameters

    Returns
    -------
    dict
        Dict with the new explainer.

    Raises
    ------
    HTTPException
        If the explainer file cannot be saved.
    """
    try:
        run: Run = db.get(Run, params.run_id)
        if not run:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Run not found"
            )

        experiment: Experiment = db.get(Experiment, run.experiment_id)
        if not experiment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Experiment not found"
            )

        dataset: Dataset = db.get(Dataset, experiment.dataset_id)
        if not dataset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found"
            )

    except exc.SQLAlchemyError as e:
        log.exception(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal database error",
        ) from e

    try:
        loaded_dataset: DashAIDataset = load_dataset(f"{dataset.file_path}/dataset")
    except FileNotFoundError as e:
        log.exception(e)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cannot load dataset from path {dataset.file_path}",
        ) from e

    explainer_class = component_registry[params.explainer_name]["class"]
    explainer = explainer_class(**params.parameters)
    explainer = explainer.fit(loaded_dataset)

    explainer_db = Explainer(
        run_id=run.id,
        dataset_id=dataset.id,
        explainer_name=params.explainer_name,
    )
    db.add(explainer_db)
    db.commit()

    explainer_id = explainer_db.id

    try:
        os.makedirs(settings.USER_EXPLAINER_PATH, exist_ok=True)
        filename = f"{explainer_id}.pkl"
        file_path = os.path.join(settings.USER_EXPLAINER_PATH, filename)
        explainer.save(file_path)
    except FileNotFoundError as e:
        log.exception(e)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Error in saving the explainer",
        ) from e

    explainer_db.explainer_path = file_path
    db.commit()
    db.refresh(explainer_db)

    return explainer_db


@router.delete("/{explainer_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_explainer(explainer_id: int, db: Session = Depends(get_db)):
    """Return the explainer with id explainer_id from the database.

    Parameters
    ----------
    explainer_id : int
        id of the explainer to delete.

    Raises
    ------
    HTTPException
        If the explainer with id explainer_id is not registered in the DB.
    """
    try:
        explainer = db.get(Explainer, explainer_id)
        if not explainer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Explainer not found",
            )

        db.delete(explainer)
        os.remove(explainer.explainer_path)
        db.commit()

    except exc.SQLAlchemyError as e:
        log.exception(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal database error",
        ) from e

    except OSError as e:
        log.exception(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete directory",
        ) from e


@router.patch("/")
async def update_component() -> None:
    """Update explainer placeholder.

    Raises
    ------
    HTTPException
        Always raises exception as it was intentionally not implemented.
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Method not implemented"
    )
