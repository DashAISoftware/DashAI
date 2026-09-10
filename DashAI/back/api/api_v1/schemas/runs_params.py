from typing import Dict, Optional, Union

from pydantic import BaseModel


class RunParams(BaseModel):
    model_session_id: int
    model_name: str
    name: str
    parameters: dict
    optimizer_name: str
    optimizer_parameters: dict
    plot_history_path: str
    plot_slice_path: str
    plot_contour_path: str
    plot_importance_path: str
    goal_metric: str
    description: Union[str, None] = None
    nested: Optional[dict] = None


class UpdateRunParams(BaseModel):
    run_name: Optional[str] = None
    run_description: Optional[str] = None
    parameters: Optional[Dict] = None
    optimizer: Optional[str] = None
    optimizer_parameters: Optional[Dict] = None
    goal_metric: Optional[str] = None
    nested: Optional[dict] = None
