from pydantic import BaseModel


# Schema for the request body
class LlamaRequest(BaseModel):
    prompt: str
    max_tokens: int = 100
