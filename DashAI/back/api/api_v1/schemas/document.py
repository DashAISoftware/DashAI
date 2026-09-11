from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel


class DocumentResponse(BaseModel):
    id: int
    session_id: int
    file_name: str
    file_type: str
    file_hash: str
    created: datetime
    last_modified: datetime
    optional_metadata: Optional[Dict[str, Any]]
    extractor: Optional[Dict[str, Any]] = None
    default_extractor: Optional[Dict[str, Any]] = None
    file_url: str
    preview_url: str


class ExtractorRef(BaseModel):
    """A ``{component, params}`` reference to an extractor configuration."""

    component: str
    params: Dict[str, Any] = {}


class UpdateExtractorRequest(BaseModel):
    """Body of ``PUT /document/{id}/extractor``."""

    extractor: ExtractorRef
