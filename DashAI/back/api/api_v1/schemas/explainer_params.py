from pydantic import BaseModel


class ExplainerParams(BaseModel):
    name: str
    run_id: int
    explainer_name: str
    parameters: dict
