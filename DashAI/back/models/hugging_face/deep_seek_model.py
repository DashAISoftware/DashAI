from typing import List

from DashAI.back.core.schema_fields import (
    BaseSchema,
    float_field,
    int_field,
    schema_field,
)
from DashAI.back.models.text_to_text_generation_model import (
    TextToTextGenerationTaskModel,
)


class DeepSeekSchema(BaseSchema):
    """Schema for DeepSeek model."""

    max_tokens: schema_field(
        int_field(ge=1),
        placeholder=100,
        description="Maximum number of tokens to generate.",
    )  # type: ignore

    temperature: schema_field(
        float_field(ge=0.0, le=1.0),
        placeholder=0.7,
        description=(
            "Sampling temperature. Higher values make the output more random, "
            "while lower values make it more focused and deterministic."
        ),
    )  # type: ignore

    frequency_penalty: schema_field(
        float_field(ge=0.0, le=2.0),
        placeholder=0.1,
        description=(
            "Penalty for repeated tokens in the output. Higher values reduce the "
            "likelihood of repetition, encouraging more diverse text generation."
        ),
    )  # type: ignore

    n_ctx: schema_field(
        int_field(ge=1),
        placeholder=4096,
        description=(
            "Maximum number of tokens the model can process in a single forward pass "
            "(context window size)."
        ),
    )  # type: ignore


class DeepSeekModel(TextToTextGenerationTaskModel):
    """DeepSeek model for text generation using llama.cpp library."""

    SCHEMA = DeepSeekSchema

    def __init__(self, **kwargs):
        try:
            from llama_cpp import Llama
        except ImportError as e:
            raise RuntimeError(
                "llama-cpp-python is not installed. "
                "Please install it to use DeepSeekModel."
            ) from e

        kwargs = self.validate_and_transform(kwargs)
        self.max_tokens = kwargs.pop("max_tokens", 100)
        self.temperature = kwargs.pop("temperature", 0.7)
        self.frequency_penalty = kwargs.pop("frequency_penalty", 0.1)
        self.n_ctx = kwargs.pop("n_ctx", 512)

        self.model_id = "TheBloke/deepseek-llm-7B-base-GGUF"
        self.filename = "*Q3_K_S.gguf"

        self.model = Llama.from_pretrained(
            repo_id=self.model_id,
            filename=self.filename,
            verbose=True,
            n_ctx=self.n_ctx,
            n_gpu_layers=-1,
        )

    def generate(self, prompt: str) -> List[str]:
        if len(prompt) > self.model.n_ctx():
            prompt = prompt[-self.model.n_ctx() :]

        """Generate text based on prompts."""

        output = self.model(
            prompt,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            frequency_penalty=self.frequency_penalty,
            stop=["Q:"],
            echo=False,
        )

        generated_text = output["choices"][0]["text"]
        clean_text = generated_text.replace(prompt, "").strip()
        return [clean_text]
