"""Base Job abstract class."""

import logging
from abc import ABCMeta, abstractmethod
from typing import Final, Optional

logger = logging.getLogger(__name__)


class BaseJob(metaclass=ABCMeta):
    """Abstract class for all Jobs."""

    TYPE: Final[str] = "Job"

    # Set to False to run this job inline in the consumer (no subprocess isolation).
    # Use for jobs that mutate in-process singletons (e.g. ComponentRegistry) or
    # that receive non-serializable arguments (e.g. a live SQLAlchemy Session).
    ISOLATED: bool = True

    # Set to True when the job mutates the consumer's ComponentRegistry so that
    # the persistent worker subprocess is restarted after this job completes,
    # ensuring the worker's DI container picks up the new registry state.
    RESETS_WORKER: bool = False

    def __init__(self, **kwargs):
        """Constructor of the ModelJob class.

        Parameters
        ----------
        kwargs: dict
            dictionary containing the parameters of the job.
        """
        job_kwargs = kwargs.pop("kwargs", {})
        self.kwargs = {**kwargs, **job_kwargs}

    def report_progress(
        self, fraction: Optional[float], message: Optional[str] = None
    ) -> None:
        """Report the job's progress to the job queue.

        Jobs opt in by calling this at meaningful checkpoints. It is safe to
        call from any job: it never raises and does nothing when the job has no
        Huey id (e.g. immediate mode used in tests) or the queue is unavailable.

        Parameters
        ----------
        fraction: Optional float
            Completion in the range 0-1, or None when the total work is unknown
            (the frontend then shows an indeterminate bar).
        message: Optional str
            Short description of the current phase.
        """
        try:
            from kink import di

            huey_id = self.kwargs.get("huey_id")
            if not huey_id:
                return

            progress = None if fraction is None else max(0.0, min(1.0, fraction)) * 100
            di["job_queue"].report_progress(huey_id, progress, message)
        except Exception as e:  # pragma: no cover - progress must never break a job
            logger.debug(f"Could not report job progress: {e}")

    @abstractmethod
    def set_status_as_delivered(self) -> None:
        """Set the status of the job as delivered."""
        raise NotImplementedError

    @abstractmethod
    def set_status_as_error(self) -> None:
        """Set the status of the job as error."""
        raise NotImplementedError

    @abstractmethod
    def get_job_name(self) -> str:
        """Get a descriptive name for the job."""
        raise NotImplementedError

    @abstractmethod
    def run() -> None:
        """Run the job."""
        raise NotImplementedError

    def on_cancel(self) -> None:  # noqa: B027
        """Called in the consumer process after the worker subprocess is killed.

        Override in subclasses to clean up partially-written artifacts (files,
        DB records) that would otherwise be left in an inconsistent state.
        The default implementation is a no-op.
        Failures must be silently swallowed — never re-raise from here.
        """


class JobError(Exception):
    """Exception raised when the job proccess fails."""
