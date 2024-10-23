from fastapi import APIRouter, HTTPException, Depends
from typing import List
from kink import di

from DashAI.back.models.llm_generation_model import LLMGenerationModel
from DashAI.back.dependencies.registry.component_registry import ComponentRegistry
from DashAI.back.api.api_v1.schemas.llm_params import LlamaRequest

router = APIRouter()


@router.post("/generate")
async def generate_text(
    request: LlamaRequest,
    component_registry: ComponentRegistry = Depends(lambda: di["component_registry"]),
):
    try:
        # Get the Llama model from the registry
        model_class = component_registry["LlamaModel"]["class"]
        model = model_class(
            model_path="/home/camilareyes/ws/llama.cpp/models/Phi-3-mini-4k-instruct-q4.gguf",  # Adjust the model path accordingly
            max_tokens=request.max_tokens,
        )

        # Generate text
        generated_text = model.generate(request.prompt)

        return {"generated_text": generated_text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating text: {str(e)}")
