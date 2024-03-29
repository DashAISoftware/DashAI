import uuid
from asyncio import Queue
from typing import Any, Coroutine, List, Optional, Tuple

from DashAI.back.dependencies.job_queues.base_job_queue import (
    BaseJobQueue,
    JobQueueError,
)
from DashAI.back.job.base_job import BaseJob


class SimpleJobQueue(BaseJobQueue):
    """JobQueue implementation using asyncio Queue."""

    queue: Queue = Queue()

    def _search_and_split(
        self, job_id: int
    ) -> Tuple[List[BaseJob], BaseJob, List[BaseJob]]:
        """Split the queue using the job with id job_id as a pivot.

        Parameters
        ----------
        job_id: int
            Id of the Job used to split the queue.

        Returns
        ----------
        tuple(List Job, Job, List Job)
            A tuple containg the first part of the queue,
            the pivot Job and the second part of the queue.

        Raises
        ----------
        JobQueueError
            If the queue is empty.
        JobQueueError
            If there is not job with job_id in the queue.
        """
        first_part = []
        target_job: BaseJob = self.queue.get_nowait()
        while target_job.id != job_id and not self.is_empty():
            first_part.append(target_job)
            target_job = self.queue.get_nowait()

        if target_job.id != job_id:
            for job in [*first_part, target_job]:
                self.queue.put_nowait(job)
            raise JobQueueError(
                f"Error trying to get job {job_id}: the job is not in the queue."
            )

        second_part = []
        while not self.is_empty():
            second_part.append(self.queue.get_nowait())

        return (first_part, target_job, second_part)

    def put(self, job: BaseJob) -> int:
        job.id = uuid.uuid4().int
        self.queue.put_nowait(job)
        return job.id

    def get(self, job_id: Optional[int] = None) -> BaseJob:
        if self.is_empty():
            raise JobQueueError(
                f"Error trying to get job {job_id}: the async queue is empty."
            )

        if job_id:
            (first_part, target_job, second_part) = self._search_and_split(job_id)
            for job in [*first_part, *second_part]:
                self.queue.put_nowait(job)
            return target_job
        else:
            return self.queue.get_nowait()

    async def async_get(self) -> Coroutine[Any, Any, BaseJob]:
        return await self.queue.get()

    def peek(self, job_id: Optional[int] = None) -> BaseJob:
        if self.is_empty():
            raise JobQueueError(
                f"Error trying to get job {job_id}: the async queue is empty."
            )

        if job_id:
            (first_part, target_job, second_part) = self._search_and_split(job_id)
            for job in [*first_part, target_job, *second_part]:
                self.queue.put_nowait(job)
            return job
        else:
            target_job: BaseJob = self.queue.get_nowait()
            tmp_queue = Queue()
            tmp_queue.put_nowait(target_job)
            while not self.is_empty():
                tmp_queue.put_nowait(self.queue.get_nowait())
            self.queue = tmp_queue
            return target_job

    def is_empty(self) -> bool:
        return self.queue.empty()

    def to_list(self) -> List[BaseJob]:
        job_list = []
        while not self.is_empty():
            job_list.append(self.queue.get_nowait())
        for job in job_list:
            self.queue.put_nowait(job)
        return job_list
