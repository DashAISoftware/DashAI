from pydantic import BaseModel


class ExplainerParams(BaseModel):
    run_id: int
    explainer: str
    parameters: dict
