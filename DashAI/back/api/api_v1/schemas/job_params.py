from pydantic import BaseModel


class JobParams(BaseModel):
    run_id: int
