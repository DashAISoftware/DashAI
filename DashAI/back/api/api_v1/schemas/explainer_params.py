from pydantic import BaseModel


class ExplainerParams(BaseModel):
    name: str
    run_id: int
    explainer: str
    parameters: dict
