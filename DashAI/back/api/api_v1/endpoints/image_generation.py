from io import BytesIO

import torch
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from kink import di
from PIL import Image

from DashAI.back.dependencies.registry.component_registry import ComponentRegistry
from DashAI.back.models.base_model import BaseModel

router = APIRouter()


@router.post(
    "/",
    response_class=StreamingResponse,
)
async def get_image(
    prompt: str,
    negative_prompt: str = None,
    num_inference_steps: int = 5,
    guidance_scale: float = 7.5,
    component_registry: ComponentRegistry = Depends(lambda: di["component_registry"]),
):
    try:
        model_class = component_registry["StableDiffusionModel"]["class"]
        model = model_class(
            num_inference_steps=num_inference_steps,
            guidance_scale=guidance_scale,
            device="cuda" if torch.cuda.is_available() else "cpu",
        )

        # Generate the image
        images = model.generate([prompt], negative_prompt=negative_prompt)

        image: Image.Image = images[0]

        # Convert PIL Image to bytes
        byte_io = BytesIO()
        image.save(byte_io, format="PNG")
        byte_io.seek(0)

        return StreamingResponse(byte_io, media_type="image/png")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating image: {str(e)}")
