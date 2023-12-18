import logging

from dependency_injector.wiring import Provide, inject
from sqlalchemy import exc

from DashAI.back.containers import Container
from DashAI.back.job.base_job import BaseJob, JobError
from DashAI.back.job_queues import BaseJobQueue

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


@inject
async def job_queue_loop(
    stop_when_queue_empties: bool,
    job_queue: BaseJobQueue = Provide[Container.job_queue],
):
    """Loop function to execute all the pending jobs in the job queue.
    If the the param stop_when_queue_empties is True, the loop returns when
    the queue empties, else it waits until  new jobs come in.

    Parameters
    ----------
    job_queue : BaseJobQueue
        The current app job queue.
    stop_when_queue_empties: bool
        boolean to set the while loop condition.

    """
    while not job_queue.is_empty() if stop_when_queue_empties else True:
        try:
            job: BaseJob = await job_queue.async_get()
            job.run()
        except exc.SQLAlchemyError as e:
            logger.exception(e)
        except JobError as e:
            logger.exception(e)
