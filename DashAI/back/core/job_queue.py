import logging

from sqlalchemy import exc

from DashAI.back.core.runner import RunnerError
from DashAI.back.dependencies.job_queues import Job

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


async def job_queue_loop(job_queue, stop_when_queue_empties: bool):
    """Loop function to execute all the pending jobs in the job queue.

    If the the param stop_when_queue_empties is True, the loop returns when
    the queue empties, else it waits until  new jobs come in.

    Parameters
    ----------
    stop_when_queue_empties: bool
        boolean to set the while loop condition.
    """
    while not job_queue.is_empty() if stop_when_queue_empties else True:
        try:
            job: Job = await job_queue.async_get()
            job.func(**job.kwargs)
        except exc.SQLAlchemyError as e:
            logger.exception(e)
        except RunnerError as e:
            logger.exception(e)
