from typing import List, Optional

import torch
from diffusers import StableDiffusionPipeline
from PIL import Image

from DashAI.back.core.schema_fields import (
    BaseSchema,
    enum_field,
    float_field,
    int_field,
    schema_field,
)
from DashAI.back.models.image_generation_model import ImageGenerationModel


class StableDiffusionSchema(BaseSchema):
    """Schema for Stable Diffusion image generation model."""

    num_inference_steps: schema_field(
        int_field(ge=1),
        placeholder=5,
        description="The number of denoising steps. More steps usually lead to a higher quality image at the expense of slower inference.",
    )  # type: ignore
    guidance_scale: schema_field(
        float_field(ge=0.0),
        placeholder=7.5,
        description="Higher guidance scale encourages images that are closer to the prompt, usually at the expense of lower image quality.",
    )  # type: ignore
    device: schema_field(
        enum_field(enum=["cuda", "cpu"]),
        placeholder="cuda",
        description="Device to run the model on. CUDA is recommended for faster generation if available.",
    )  # type: ignore


class StableDiffusionModel(ImageGenerationModel):
    """Stable Diffusion model for image generation."""

    SCHEMA = StableDiffusionSchema

    def __init__(self, **kwargs):
        kwargs = self.validate_and_transform(kwargs)
        self.model_id = "stabilityai/stable-diffusion-2-1"
        self.num_inference_steps = kwargs.pop("num_inference_steps")
        self.guidance_scale = kwargs.pop("guidance_scale")
        self.device = kwargs.pop("device")

        self.pipeline = StableDiffusionPipeline.from_pretrained(
            self.model_id,
            torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
        ).to(self.device)

    def generate(
        self, prompt: str, negative_prompt: Optional[str] = None
    ) -> List[Image.Image]:
        """Generate images based on text prompts."""
        image = self.pipeline(
            prompt,
            negative_prompt=negative_prompt,
            num_inference_steps=self.num_inference_steps,
            guidance_scale=self.guidance_scale,
        ).images[0]
        return image

    def save(self, filename: str) -> None:
        self.pipeline.save_pretrained(filename)

    @classmethod
    def load(cls, filename: str) -> "StableDiffusionModel":
        pipeline = StableDiffusionPipeline.from_pretrained(filename)
        model = cls(
            model_id=filename,
            num_inference_steps=5,
            guidance_scale=7.5,
            device="cuda" if torch.cuda.is_available() else "cpu",
        )
        model.pipeline = pipeline
        return model
