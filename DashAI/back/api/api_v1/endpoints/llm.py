from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from llama_cpp import Llama
from kink import inject

from DashAI.back.api.api_v1.schemas.llm_params import LlamaRequest

router = APIRouter()

# Initialize the model with the pre-trained file
llm = Llama.from_pretrained(
    repo_id="Qwen/Qwen2-0.5B-Instruct-GGUF",  # Hugging Face repository with the pre-trained model
    filename="*q8_0.gguf",  # The model file within the repository (uses a .gguf file)
    verbose=True,  # To get more information about the download and loading process
)


# Define an endpoint to generate text using the model
@router.post("/chat")
@inject
async def generate_text(request: LlamaRequest):
    try:
        # Generate text using llama.cpp
        output = llm(
            f"Q: {request.prompt} A:",  # Use the prompt from the request
            max_tokens=request.max_tokens,  # Use the max_tokens value from the request
            stop=["\n"],  # Optional parameter to stop the generation
            echo=True,  # Echo the prompt in the response
        )
        return {"output": output["choices"][0]["text"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating text: {str(e)}")


# Define a test endpoint to check if the service is running
@router.get("/test")
@inject
async def test():
    return {"message": "Endpoint running correctly"}
