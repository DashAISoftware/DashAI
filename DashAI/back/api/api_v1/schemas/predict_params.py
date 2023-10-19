from pydantic import BaseModel


class PredictParams(BaseModel):
    run_id: int
