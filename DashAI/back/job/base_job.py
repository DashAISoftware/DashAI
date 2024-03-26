"""Base Job abstract class."""
import logging
from abc import ABCMeta, abstractmethod
from typing import Final

from dependency_injector.wiring import Provide, inject
from sqlalchemy import exc

from DashAI.back.dependencies.database.models import Run

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)


class BaseJob(metaclass=ABCMeta):
    """Abstract class for all Jobs."""

    TYPE: Final[str] = "Job"

    def __init__(self, **kwargs):
        """Constructor of the ModelJob class.

        Parameters
        ----------
        kwargs: dict
            dictionary containing the parameters of the job.
        """
        job_kwargs = kwargs.pop("kwargs", {})
        self.kwargs = {**kwargs, **job_kwargs}

    @inject
    def deliver_job(self, session_factory=Provide["db"]) -> None:
        """Set the status of the job as delivered."""
        with session_factory.session() as db:
            run_id: int = self.kwargs["run_id"]
            run: Run = db.get(Run, run_id)
            if not run:
                raise JobError(
                    f"Cannot deliver job: Run {run_id} does not exist in DB."
                )
            try:
                run.set_status_as_delivered()
                db.commit()
            except exc.SQLAlchemyError as e:
                log.exception(e)
                raise JobError(
                    "Internal database error",
                ) from e

    @inject
    def start_job(self, session_factory=Provide["db"]) -> None:
        """Set the status of the job as started."""
        with session_factory.session() as db:
            run_id: int = self.kwargs["run_id"]
            run: Run = db.get(Run, run_id)
            if not run:
                raise JobError(f"Cannot start job: Run {run_id} does not exist in DB.")
            try:
                run.set_status_as_started()
                db.commit()
            except exc.SQLAlchemyError as e:
                log.exception(e)
                raise JobError(
                    "Internal database error",
                ) from e

    @inject
    def finish_job(self, session_factory=Provide["db"]) -> None:
        """Set the status of the job as finished."""
        with session_factory.session() as db:
            run_id: int = self.kwargs["run_id"]
            run: Run = db.get(Run, run_id)
            if not run:
                raise JobError(f"Cannot finish job: Run {run_id} does not exist in DB.")
            try:
                run.set_status_as_finished()
                db.commit()
            except exc.SQLAlchemyError as e:
                log.exception(e)
                raise JobError(
                    "Internal database error",
                ) from e

    @abstractmethod
    def get_args(self) -> dict:
        """Get the arguements to pass to run method."""
        raise NotImplementedError

    @abstractmethod
    def store_results(self, results: dict) -> None:
        """Store the results of the job."""
        raise NotImplementedError

    @abstractmethod
    def run() -> None:
        """Run the job."""
        raise NotImplementedError


class JobError(Exception):
    """Exception raised when the job proccess fails."""
