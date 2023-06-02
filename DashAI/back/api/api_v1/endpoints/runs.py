import logging
import os
from typing import Union

from fastapi import APIRouter, Depends, Response, status
from fastapi.exceptions import HTTPException
from sqlalchemy import exc, select
from sqlalchemy.orm import Session

from DashAI.back.api.deps import get_db
from DashAI.back.database.models import Experiment, Run, RunStatus

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)

router = APIRouter()


@router.get("/")
async def get_runs(experiment_id: int | None = None, db: Session = Depends(get_db)):
    """Retrieve a list of runs from the DB.

    The runs can be filtered by experiment_id if the parameter is passed.

    Parameters
    ----------
    experiment_id: int | None, optional
        If specified, the function will return all the runs associated with
        the experiment, by default None.

    Returns
    -------
    list[dict]
        A list with the information of all selected runs.

    Raises
    ------
    HTTPException
        If the experiment is not registered in the DB.
    """
    try:
        if experiment_id is not None:
            runs = db.scalars(
                select(Run).where(Run.experiment_id == experiment_id)
            ).all()
            if not runs:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Runs assoc with Experiment not found",
                )
        else:
            runs = db.query(Run).all()
    except exc.SQLAlchemyError as e:
        log.exception(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal database error",
        ) from e
    return runs


@router.get("/{run_id}")
async def get_run_by_id(run_id: int, db: Session = Depends(get_db)):
    """
    Returns the run with the specified id.

    Returns
    -------
    dict
        All the information of the selected run.

    Raises
    ------
    HTTPException
        If the run is not registered in the DB.
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
        ) from e
    return run


@router.post("/", status_code=status.HTTP_201_CREATED)
async def upload_run(
    experiment_id: int,
    model_name: str,
    name: str,
    parameters: dict,
    description: str | None = None,
    db: Session = Depends(get_db),
):
    """
    Endpoint to create a run.

    Parameters
    ----------
    experiment_id : int
        Id of the Experiment linked to the run.
    model_name : str
        Name of the Model linked to the run.
    name : str
        Name of the run
    parameters : dict
        Parameters to instantiate the run.
    description: str | None, optional
        A brief description of the run, by default None.

    Returns
    -------
    dict
        A dictionary with the new run on the database

    Raises
    ------
    HTTPException
        If the experiment with id experiment_id is not registered in the DB.
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
        ) from e


@router.delete("/{run_id}")
async def delete_run(run_id: int, db: Session = Depends(get_db)):
    """
    Deletes the run with id run_id from the DB.

    Parameters
    ----------
    run_id : int
        id of the run to delete.

    Returns
    -------
    Response with code 204 NO_CONTENT

    Raises
    ------
    HTTPException
        If the run is not registered in the DB.
    HTTPException
        If the run was trained but the run_path does not exists.
    """
    try:
        run = db.get(Run, run_id)
        if not run:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Run not found"
            )
        db.delete(run)
        if run.status == RunStatus.FINISHED:
            os.remove(run.run_path)
        db.commit()
        return Response(status_code=status.HTTP_204_NO_CONTENT)
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


@router.patch("/{run_id}")
async def update_run(
    run_id: int,
    db: Session = Depends(get_db),
    run_name: Union[str, None] = None,
    run_description: Union[str, None] = None,
    parameters: Union[dict, None] = None,
):
    """
    Updates the run information with id run_id from the DB.

    Parameters
    ----------
    run_id : int
        The id of the run to update.
    run_name : str | None, optional
        The new name of the run, by default None.
    run_description : str | None, optional
        The new description of the run, by default None.
    parameters : dict | None, optional
        The new parameters of the run, by default None.

    Returns
    -------
    dict
        A dict containing the updated record

    Raises
    ------
    HTTPException
        If no parameters passed.
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
        ) from e
