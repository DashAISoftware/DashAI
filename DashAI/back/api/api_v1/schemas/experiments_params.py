from pydantic import BaseModel


class ExperimentParams(BaseModel):
    dataset_id: int
    task_name: str
    name: str
    input_columns: str
    output_columns: str
    splits: str
