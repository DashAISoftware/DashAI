from pydantic import BaseModel


class RunnerParams(BaseModel):
    run_id: int
