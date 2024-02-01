import logging

from sqlalchemy import exc

from DashAI.back.core.config import job_queue
from DashAI.back.job.base_job import BaseJob, JobError

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)


async def job_queue_loop(stop_when_queue_empties: bool):
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
            job: BaseJob = await job_queue.async_get()
            job.run()
        except exc.SQLAlchemyError as e:
            log.exception(e)
        except JobError as e:
            log.exception(e)