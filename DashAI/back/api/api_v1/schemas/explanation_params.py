from pydantic import BaseModel


class GlobalExplanationParams(BaseModel):
    name: str
    run_id: int
    explainer_name: str
    parameters: dict
