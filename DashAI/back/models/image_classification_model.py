from DashAI.back.models.base_model import BaseModel


class ImageClassificationModel(BaseModel):
    """Class for models associated to ImageClassificationTask."""

    COMPATIBLE_COMPONENTS = ["ImageClassificationTask"]
