import logging
import os
from typing import Union

from fastapi import APIRouter, Depends, Response, status
from fastapi.exceptions import HTTPException
from kink import di, inject
from sqlalchemy import exc, select
from sqlalchemy.orm import sessionmaker

from DashAI.back.api.api_v1.schemas.runs_params import RunParams
from DashAI.back.dependencies.database.models import Experiment, Run, RunStatus

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)

router = APIRouter()


@router.get("/")
@inject
async def get_runs(
    experiment_id: Union[int, None] = None,
    session_factory: sessionmaker = Depends(lambda: di[sessionmaker]),
):
    """Retrieve a list of the stored experiment runs in the database.

    The runs can be filtered by experiment_id if the parameter is passed.

    Parameters
    ----------
    experiment_id: Union[int, None], optional
        If specified, the function will return all the runs associated with
        the experiment, by default None.
    session_factory : Callable[..., ContextManager[Session]]
        A factory that creates a context manager that handles a SQLAlchemy session.
        The generated session can be used to access and query the database.

    Returns
    -------
    List[dict]
        A list with all selected runs.

    Raises
    ------
    HTTPException
        If the experiment is not registered in the DB.
    """
    with session_factory() as db:
        try:
            if experiment_id is not None:
                runs = db.scalars(
                    select(Run).where(Run.experiment_id == experiment_id)
                ).all()
                if not runs:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Runs associated with Experiment not found",
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
@inject
async def get_run_by_id(
    run_id: int,
    session_factory: sessionmaker = Depends(lambda: di[sessionmaker]),
):
    """Retrieve the run associated with the provided ID.

    Parameters
    ----------
    run_id : int
        ID of the dataset to retrieve.
    session_factory : Callable[..., ContextManager[Session]]
        A factory that creates a context manager that handles a SQLAlchemy session.
        The generated session can be used to access and query the database.

    Returns
    -------
    dict
        All the information of the selected run.

    Raises
    ------
    HTTPException
        If the run is not registered in the DB.
    """
    with session_factory() as db:
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
@inject
async def upload_run(
    params: RunParams,
    session_factory: sessionmaker = Depends(lambda: di[sessionmaker]),
):
    """Create a new run.

    Parameters
    ----------
    params : int
        The parameters of the new run, which includes the experiment, model name, run
        name and description, among others.
    session_factory : Callable[..., ContextManager[Session]]
        A factory that creates a context manager that handles a SQLAlchemy session.
        The generated session can be used to access and query the database.

    Returns
    -------
    dict
        A dictionary with the new run on the database

    Raises
    ------
    HTTPException
        If the experiment with id experiment_id is not registered in the DB.
    """
    with session_factory() as db:
        try:
            experiment = db.get(Experiment, params.experiment_id)
            if not experiment:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="Experiment not found"
                )
            run = Run(
                experiment_id=params.experiment_id,
                model_name=params.model_name,
                parameters=params.parameters,
                name=params.name,
                description=params.description,
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
@inject
async def delete_run(
    run_id: int,
    session_factory: sessionmaker = Depends(lambda: di[sessionmaker]),
):
    """Delete the run associated with the provided ID from the database.

    Parameters
    ----------
    run_id : int
        ID of the run to be deleted.
    session_factory : Callable[..., ContextManager[Session]]
        A factory that creates a context manager that handles a SQLAlchemy session.
        The generated session can be used to access and query the database.

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
    with session_factory() as db:
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
@inject
async def update_run(
    run_id: int,
    run_name: Union[str, None] = None,
    run_description: Union[str, None] = None,
    parameters: Union[dict, None] = None,
    session_factory: sessionmaker = Depends(lambda: di[sessionmaker]),
):
    """Updates the run with the provided ID.

    Parameters
    ----------
    run_id : int
        ID of the run to update.
    run_name : Union[str, None], optional
        The new name of the run, by default None.
    run_description : Union[str, None], optional
        The new description of the run, by default None.
    parameters : Union[dict, None], optional
        The new parameters of the run, by default None.
    session_factory : Callable[..., ContextManager[Session]]
        A factory that creates a context manager that handles a SQLAlchemy session.
        The generated session can be used to access and query the database.

    Returns
    -------
    Dict
        A dictionary containing the updated run record.

    Raises
    ------
    HTTPException
        If no parameters passed.
    """
    with session_factory() as db:
        try:
            run = db.get(Run, run_id)
            if run_name:
                setattr(run, "name", run_name)
            if run_description:
                setattr(run, "description", run_description)
            if parameters:
                setattr(run, "parameters", parameters)
            if run_name or run_description or parameters:
                db.commit()
                db.refresh(run)
                return run
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
