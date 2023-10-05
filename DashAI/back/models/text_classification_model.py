from DashAI.back.models.base_model import BaseModel


class TextClassificationModel(BaseModel):
    """Class for models associated to TextClassificationTask."""

    COMPATIBLE_COMPONENTS = ["TextClassificationTask"]
