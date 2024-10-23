from DashAI.back.models.base_model import BaseModel


class LLMGenerationModel(BaseModel):
    """Class for models associated to LLMGenerationProcess."""

    COMPATIBLE_COMPONENTS = ["LLMGenerationProcess"]
