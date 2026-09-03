from typing import Any, Dict, Optional

from pydantic import BaseModel


class RAGPromptSchema(BaseModel):
    """Schema for creating a RAG prompt.

    Attributes:
        class_name: Registered prompt component class name.
        name: Human-readable name for the prompt.
        parameters: Optional configuration dict including template(s).
    """

    class_name: str
    name: str
    parameters: Optional[Dict[str, Any]] = None
