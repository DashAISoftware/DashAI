from typing import Optional

from pydantic import BaseModel


class PredictionCreationParams(BaseModel):
    run_id: int
    dataset_id: Optional[int] = None
    split: Optional[str] = None
