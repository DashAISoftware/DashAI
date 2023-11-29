from pydantic import BaseModel


class ExplainerParams(BaseModel):
    run_id: int
    explainer_name: str
    parameters: dict
