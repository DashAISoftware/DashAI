from pydantic import BaseModel


class GlobalExplainerParams(BaseModel):
    run_id: int
    explainer_name: str
    parameters: dict


class LocalExplainerParams(BaseModel):
    run_id: int
    explainer_name: str
    dataset_id: int
    parameters: dict
    fit_parameters: dict
    scope: dict


class ValidateDatasetParams(BaseModel):
    run_id: int
    dataset_id: int


class ValidDatasetsParams(BaseModel):
    run_id: int
