from enum import Enum
from typing import Any, Callable, Dict, Optional

from pydantic import BaseModel, model_serializer
from sqlalchemy.orm import Session


class JobType(Enum):
    """Enumeration for job types."""

    runner = 0


class Job(BaseModel):
    """Model for abstracting a job."""

    id: Optional[int] = None
    func: Callable[[int, Session], None]
    type: JobType
    kwargs: dict

    @model_serializer
    def ser_job(self) -> Dict[str, Any]:
        """Returns a dict representation of the Job.

        Returns
        ----------
        dict
            dictionary with most of the fields of the Job.
        """
        return {"id": self.id, "type": self.type, "run_id": self.kwargs["run_id"]}
