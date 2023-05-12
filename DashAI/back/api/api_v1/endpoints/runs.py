import logging
from typing import Union

from fastapi import APIRouter, Depends, Response, status
from fastapi.exceptions import HTTPException
from sqlalchemy import exc, select
from sqlalchemy.orm import Session

from DashAI.back.api.deps import get_db
from DashAI.back.database.models import Experiment, Run

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)

router = APIRouter()


@router.get("/")
async def get_run(run_id: int, db: Session = Depends(get_db)):
    """
    Returns the run with the spécified id.

    Returns
    -------
    JSON
        run JSON
    """

    try:
        run = db.get(Run, run_id)
        if not run:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Run not found",
            )
    except exc.SQLAlchemyError as e:
        log.exception(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal database error",
        )
    return run


@router.get("/list/{experiment_id}")
async def get_run_from_experiment(experiment_id: int, db: Session = Depends(get_db)):
    """
    Returns the runs associated with the specified experiment_id from the database.

    Parameters
    ----------
    experiment_id : int
        id of the experiment assoc with the runs to query.

    Returns
    -------
    List[JSON]
        List of run JSON associated with the specified experiment id.
    """
    try:
        runs = db.execute(select(Run).where(Run.experiment_id == experiment_id)).all()
        if not runs:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Runs assoc with Experiment not found",
            )
    except exc.SQLAlchemyError as e:
        log.exception(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal database error",
        )
    return runs


@router.post("/", status_code=status.HTTP_201_CREATED)
async def upload_run(
    experiment_id: int,
    model_name: str,
    name: str,
    parameters: dict,
    description: str = "",
    db: Session = Depends(get_db),
):
    """
    Endpoint to create run of an experiment.

    Parameters
    ----------
    experiment_id : int
        Id of the Experiment linked to the run.
    mdoel_name : str
        Name of the Model linked to the run.
    name : str
        Name of the run
    parameters : JSON
        Parameters of the run.
    Returns
    -------
    JSON
        JSON with the new run on the database
    """
    try:
        experiment = db.get(Experiment, experiment_id)
        if not experiment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Experiment not found"
            )
        run = Run(
            experiment_id=experiment_id,
            model_name=model_name,
            parameters=parameters,
            run_name=name,
            run_description=description,
        )
        db.add(run)
        db.commit()
        db.refresh(run)
        return run
    except exc.SQLAlchemyError as e:
        log.exception(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal database error",
        )


@router.delete("/{run_id}")
async def delete_run(run_id: int, db: Session = Depends(get_db)):
    """
    Deletes the run with id run_id from the database.

    Parameters
    ----------
    run_id : int
        id of the run to delete.

    Returns
    -------
    Response with code 204 NO_CONTENT
    """
    try:
        run = db.get(Run, run_id)
        if not run:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Run not found"
            )
        db.delete(run)
        db.commit()
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except exc.SQLAlchemyError as e:
        log.exception(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal database error",
        )


@router.patch("/{run_id}")
async def update_run(
    run_id: int,
    db: Session = Depends(get_db),
    run_name: Union[str, None] = None,
    run_description: Union[str, None] = None,
    parameters: Union[dict, None] = None,
):
    """
    Updates the run information with id run_id from the database.

    Parameters
    ----------
    run_id : int
        id of the run to update.
    run_name : Optional str
        new name of the run.
    run_description : Optional str
        new description of the run.
    parameters : Optional JSON
        new parameters of the run.

    Returns
    -------
    JSON
        JSON containing the updated record
    """
    try:
        run = db.get(Run, run_id)
        if run_name:
            setattr(run, "run_name", run_name)
        if run_description:
            setattr(run, "run_description", run_description)
        if parameters:
            setattr(run, "parameters", parameters)
        if run_name or run_description or parameters:
            db.commit()
            db.refresh(run)
            return run
        else:
            raise HTTPException(
                status_code=status.HTTP_304_NOT_MODIFIED, detail="Record not modified"
            )
    except exc.SQLAlchemyError as e:
        log.exception(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal database error",
        )
