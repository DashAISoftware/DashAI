from DashAI.back.models.base_model import BaseModel


class TextClassificationModel(BaseModel):
    """
    Class for models associated to TextClassificationTask
    """

    _compatible_tasks = ["TextClassificationTask"]
