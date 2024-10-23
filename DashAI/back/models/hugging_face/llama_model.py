from typing import List
from llama_cpp import Llama

from DashAI.back.core.schema_fields import (
    BaseSchema,
    int_field,
    schema_field,
)

from DashAI.back.models.llm_generation_model import LLMGenerationModel


class LlamaSchema(BaseSchema):
    """Schema for Llama text generation model."""

    max_tokens: schema_field(
        int_field(ge=1),
        placeholder=100,
        description="Maximum number of tokens to generate.",
    )  # type: ignore


class LlamaModel(LLMGenerationModel):
    """Llama model for text generation using llama.cpp library."""

    SCHEMA = LlamaSchema

    def __init__(self, model_path: str, **kwargs):
        kwargs = self.validate_and_transform(kwargs)
        self.model = Llama(model_path=model_path)
        self.max_tokens = kwargs.pop("max_tokens", 100)

    def generate(self, prompt: str) -> str:
        """Generate text based on prompts."""
        output = self.model(
            f"Q: {prompt} A:", max_tokens=self.max_tokens, stop=["\n", "Q:"], echo=True
        )
        return output["choices"][0]["text"]

    def save(self, filename: str) -> None:
        # Not implemented for llama as the model is pre-trained
        pass

    @classmethod
    def load(cls, filename: str) -> "LlamaModel":
        # Load the model from a given path
        return cls(model_path=filename)
