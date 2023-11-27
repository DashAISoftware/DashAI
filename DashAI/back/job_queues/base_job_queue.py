from abc import ABCMeta, abstractmethod
from typing import Any, Coroutine, List, Optional

from DashAI.back.job.base_job import BaseJob  # noqa


class BaseJobQueue(metaclass=ABCMeta):
    """Abstract class for all Jobs Queues."""

    @abstractmethod
    def put(self, job: BaseJob) -> int:
        """Put a job at the end of the queue.

        Parameters
        ----------
        job: Job
            Job to put in the queue.

        Returns
        ----------
        int
            The id of the job.
        """
        raise NotImplementedError

    @abstractmethod
    def get(self, job_id: Optional[int] = None) -> BaseJob:
        """Extract the job with id job_id from the queue.
        If the id is not specified, it extracts the first job in the queue.

        Parameters
        ----------
        job_id: Optional int
            id of the job to get.

        Returns
        ----------
        Job
            Extracted job from the queue.

        Raises
        ----------
        JobQueueError
            If the queue is empty.
        JobQueueError
            If there is not job with job_id in the queue.
        """
        raise NotImplementedError

    @abstractmethod
    async def async_get(self) -> Coroutine[Any, Any, BaseJob]:
        """Tries to extract a Job from the queue,
        if the queue is empty waits until it has a Job to extract.

        Returns
        ----------
        Job
            Extracted job from the queue.
        """
        raise NotImplementedError

    @abstractmethod
    def peek(self, job_id: Optional[int] = None) -> BaseJob:
        """Retrieve the job with id job_id without removing it from the queue.
        If the id is not specified, it retrieves the first job in the queue.

        Parameters
        ----------
        job_id: Optional int
            id of the job to peek.

        Returns
        -------
        Job
            Retrived Job from the queue.

        Raises
        ----------
        JobQueueError
            If the queue is empty.
        JobQueueError
            If there is not job with job_id in the queue.
        """
        raise NotImplementedError

    @abstractmethod
    def is_empty(self) -> bool:
        """Predicate that indicates if the queue is empty.

        Returns
        ----------
        bool
            If the queue is empty.
        """
        raise NotImplementedError

    @abstractmethod
    def to_list(self) -> List[BaseJob]:
        """List all the jobs in the queue and returns them.

        Returns
        ----------
        list Job
            All the Jobs in the queue.
        """
        raise NotImplementedError


class JobQueueError(Exception):
    """Exception raised when a method of the job queue fails."""
