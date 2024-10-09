from DashAI.back.models.base_model import BaseModel


class RegressionModel(BaseModel):
    """Class for models associated to RegressionTask."""

    COMPATIBLE_COMPONENTS = ["RegressionTask"]
