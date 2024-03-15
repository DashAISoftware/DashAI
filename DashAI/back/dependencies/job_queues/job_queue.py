import asyncio
import logging
from multiprocessing import Process

from dependency_injector.wiring import Provide, inject

from DashAI.back.containers import Container
from DashAI.back.dependencies.job_queues import BaseJobQueue
from DashAI.back.job.base_job import BaseJob, JobError

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


@inject
async def job_queue_loop(
    component_registry=Provide[Container.component_registry],
    session_factory=Provide[Container.db.provided.session],
    config=Provide[Container.config],
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
    try:
        while True:
            job: BaseJob = await job_queue.async_get()
            job_process = Process(
                target=job.run,
                daemon=True,
            )
            job_process.start()

            while job_process.is_alive():
                logger.debug(f"Awaiting {job.id} process for 1 second.")
                await asyncio.sleep(1)

            job_process.join()

    except JobError as e:
        logger.exception(e)
        raise RuntimeError(
            f"Error in the training execution loop: {e}.\nShutting down the app."
        ) from e
    except KeyboardInterrupt:
        logger.info("Shutting down the app")
        return
