from abc import ABCMeta, abstractmethod
from enum import Enum
from typing import Any, Callable, Coroutine, List

from pydantic import BaseModel


class JobType(Enum):
    """Enumeration for job types."""

    runner = 0


class Job(BaseModel):
    """Model for abstracting a job."""

    id: int | None
    func: Callable[[int], None]
    type: JobType
    kwargs: dict

    def to_dict(self) -> dict:
        """Returns a dict representation of the Job.

        Returns
        ----------
        dict
            dictionary with most of the fields of the Job.
        """
        return {"id": self.id, "type": self.type, "kwargs": self.kwargs}


class JobQueueError(Exception):
    """Exception raised when a method of the job queue fails."""


class BaseJobQueue(metaclass=ABCMeta):
    """Abstract class for all Jobs Queues."""

    @abstractmethod
    def put(self, job: Job) -> int:
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
    def get(self, job_id: int | None = None) -> Job:
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
    async def async_get(self) -> Coroutine[Any, Any, Job]:
        """Tries to extract a Job from the queue,
        if the queue is empty waits until it has a Job to extract.

        Returns
        ----------
        Job
            Extracted job from the queue.
        """
        raise NotImplementedError

    @abstractmethod
    def peek(self, job_id: int | None = None) -> Job:
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
    def to_list(self) -> List[Job]:
        """List all the jobs in the queue and returns them.

        Returns
        ----------
        list Job
            All the Jobs in the queue.
        """
        raise NotImplementedError
