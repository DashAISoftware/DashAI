from DashAI.back.models.base_model import BaseModel


class TranslationModel(BaseModel):
    """Class for models associated to TranslationTask."""

    COMPATIBLE_COMPONENTS = ["TranslationTask"]
