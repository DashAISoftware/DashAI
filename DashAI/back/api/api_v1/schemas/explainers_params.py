from pydantic import BaseModel


class GlobalExplainerParams(BaseModel):
    name: str
    run_id: int
    explainer_name: str
    parameters: dict


class LocalExplainerParams(BaseModel):
    name: str
    run_id: int
    explainer_name: str
    dataset_id: int
    parameters: dict
    fit_parameters: dict
