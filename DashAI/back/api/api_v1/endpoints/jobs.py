import logging
from typing import Callable, ContextManager

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, BackgroundTasks, Depends, Response, status
from fastapi.exceptions import HTTPException
from sqlalchemy import exc
from sqlalchemy.orm import Session

from DashAI.back.api.api_v1.schemas.job_params import JobParams
from DashAI.back.containers import Container
from DashAI.back.core.job_queue import job_queue_loop
from DashAI.back.core.runner import execute_run
from DashAI.back.database.models import Run
from DashAI.back.job_queues import BaseJobQueue, Job, JobQueueError, JobType

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/start/")
async def start_job_queue(
    background_tasks: BackgroundTasks,
    stop_when_queue_empties: bool = False,
):
    """Start the job queue to begin processing the jobs inside the jobs queue.
    If the param stop_when_queue_empties is True, the loop stops when the job queue
    becomes empty.

    Parameters
    ----------
    stop_when_queue_empties: Optional bool
        boolean to set the behavior of the loop.

    Returns
    -------
    Response
        response with code 202 ACCEPTED
    """
    background_tasks.add_task(job_queue_loop, stop_when_queue_empties)
    return Response(status_code=status.HTTP_202_ACCEPTED)


@router.get("/")
@inject
async def get_jobs(
    job_queue: BaseJobQueue = Provide[Container.job_queue],
):
    """Return all the jobs in the job queue.

    Parameters
    ----------
    job_queue : BaseJobQueue
        The current app job queue.

    Returns
    ----------
    List[dict]
        A list of dict containing the Jobs.
    """
    all_jobs = job_queue.to_list()
    return all_jobs


@router.get("/{job_id}")
@inject
async def get_job(
    job_id: int,
    job_queue: BaseJobQueue = Provide[Container.job_queue],
):
    """Return the selected job from the job queue

    Parameters
    ----------
    job_id: int
        id of the Job to get.
    job_queue : BaseJobQueue
        The current app job queue.

    Returns
    ----------
    dict
        A dict containing the Job information.

    Raises
    ----------
    HTTPException
        If is not posible to get the job from the job queue.
    """
    try:
        job = job_queue.peek(job_id)
    except JobQueueError as e:
        logger.exception(e)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found",
        ) from e
    return job


@router.post("/runner/", status_code=status.HTTP_201_CREATED)
@inject
async def enqueue_runner_job(
    params: JobParams,
    session_factory: Callable[..., ContextManager[Session]] = Depends(
        Provide[Container.db.provided.session]
    ),
    job_queue: BaseJobQueue = Provide[Container.job_queue],
):
    """Create a runner job and put it in the job queue.

    Parameters
    ----------
    run_id : int
        Id of the Run to train and evaluate.
    session_factory : Callable[..., ContextManager[Session]]
        A factory that creates a context manager that handles a SQLAlchemy session.
        The generated session can be used to access and query the database.
    job_queue : BaseJobQueue
        The current app job queue.

    Returns
    -------
    dict
        dict with the new job on the database
    """
    with session_factory() as db:
        try:
            run: Run = db.get(Run, params.run_id)
            if not run:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="Run not found"
                )
        except exc.SQLAlchemyError as e:
            logger.exception(e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal database error",
            ) from e

    job = Job(
        func=execute_run,
        type=JobType.runner,
        kwargs={"run_id": params.run_id, "db": db},
    )
    job_queue.put(job)

    try:
        run.set_status_as_delivered()
        db.commit()
    except exc.SQLAlchemyError as e:
        logger.exception(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal database error",
        ) from e

    return job


@router.delete("/")
@inject
async def cancel_job(
    job_id: int,
    job_queue: BaseJobQueue = Provide[Container.job_queue],
):
    """Delete the job with id job_id from the job queue.

    Parameters
    ----------
    job_id : int
        id of the job to delete.
    job_queue : BaseJobQueue
        The current app job queue.

    Returns
    -------
    Response
        response with code 204 NO_CONTENT

    Raises
    ----------
    HTTPException
        If is not posible to get the job from the job queue.
    """
    try:
        job_queue.get(job_id)
    except JobQueueError as e:
        logger.exception(e)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found",
        ) from e
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.patch("/")
async def update_job():
    """Placeholder for job update.

    Raises
    ------
    HTTPException
        Always raises exception as it was intentionally not implemented.
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Method not implemented"
    )
