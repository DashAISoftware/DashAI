import asyncio
import logging
from multiprocessing import Pipe, Process

from dependency_injector.wiring import Provide, inject

from DashAI.back.containers import Container
from DashAI.back.dependencies.job_queues import BaseJobQueue
from DashAI.back.job.base_job import BaseJob, JobError

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
    stop_when_queue_empties: bool
        boolean to set the while loop condition.
    job_queue : BaseJobQueue
        The current app job queue.

    """
    try:
        while not (stop_when_queue_empties and job_queue.is_empty()):
            # Get the job from the queue
            job: BaseJob = await job_queue.async_get()
            parent_conn, child_conn = Pipe()

            # Get Job Arguments
            job_args = job.get_args()
            job_args["pipe"] = child_conn

            # Create the Proccess to run the job
            job_process = Process(target=job.run, kwargs=job_args, daemon=True)

            # Launch the job
            job.start_job()

            # Proccess managment
            job_process.start()

            # Wait until the job fails or the child send the resutls
            while job_process.is_alive() and not parent_conn.poll():
                logger.debug(f"Awaiting {job.id} process for 1 second.")
                await asyncio.sleep(1)

            # Check if the job fails
            if not job_process.is_alive() and job_process.exitcode != 0:
                job.terminate_job()
                continue

            job_results = parent_conn.recv()
            parent_conn.close()

            # Wait until the job returns
            while job_process.is_alive():
                logger.debug(f"Awaiting {job.id} process for 1 second.")
                await asyncio.sleep(1)
            job_process.join()

            # Finish the job
            job.finish_job()

            # Store the results of the job
            job.store_results(**job_results)

    except JobError as e:
        logger.exception(e)
        raise RuntimeError(
            f"Error in the training execution loop: {e}.\nShutting down the app."
        ) from e
    except KeyboardInterrupt:
        logger.info("Shutting down the app")
        return
