from fastapi import APIRouter, Depends, HTTPException, status
from kink import di
from sqlalchemy.orm import sessionmaker

from DashAI.back.api.api_v1.schemas.RAG_prompt import (
    RAGPromptSchema,
    RAGPromptUpdateSchema,
)
from DashAI.back.dependencies.database.models import GenerativeSession
from DashAI.back.dependencies.registry import ComponentRegistry
from DashAI.back.models.RAG.exceptions import (
    RAGDatabaseError,
    RAGPromptError,
    RAGPromptValidationError,
)
from DashAI.back.services.RAG.prompt_service import PromptService

router = APIRouter()


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_RAG_prompt(  # noqa: N802
    prompt: RAGPromptSchema,
    component_registry: ComponentRegistry = Depends(lambda: di["component_registry"]),
    session_factory: sessionmaker = Depends(lambda: di["session_factory"]),
):
    """Create a new RAGPrompt entry in the database."""

    with session_factory() as db:
        try:
            service = PromptService(db, component_registry)
            result = service.create(
                prompt.class_name, prompt.name, prompt.parameters or {}
            )
            return {"id": result.id}
        except RAGPromptValidationError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
            ) from e
        except RAGDatabaseError as e:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A prompt with these parameters already exists.",
            ) from e
        except RAGPromptError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
            ) from e


@router.patch("/{prompt_id}", status_code=status.HTTP_200_OK)
async def update_RAG_prompt(  # noqa: N802
    prompt_id: int,
    prompt: RAGPromptUpdateSchema,
    component_registry: ComponentRegistry = Depends(lambda: di["component_registry"]),
    session_factory: sessionmaker = Depends(lambda: di["session_factory"]),
):
    """Update an existing prompt in place."""

    with session_factory() as db:
        try:
            service = PromptService(db, component_registry)
            result = service.update(
                prompt_id,
                name=prompt.name,
                parameters=prompt.parameters,
            )
            return result
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
            ) from e


@router.post("/{prompt_id}/sessions/{session_id}", status_code=status.HTTP_201_CREATED)
async def update_RAG_prompt_for_session(  # noqa: N802
    prompt_id: int,
    session_id: int,
    prompt: RAGPromptUpdateSchema,
    component_registry: ComponentRegistry = Depends(lambda: di["component_registry"]),
    session_factory: sessionmaker = Depends(lambda: di["session_factory"]),
):
    """Create a session-scoped copy of a prompt and attach it to the session."""

    with session_factory() as db:
        try:
            service = PromptService(db, component_registry)
            prompt_result = service.create_session_copy(
                prompt_id,
                session_id,
                parameters=prompt.parameters,
                name=prompt.name,
            )
            session = db.get(GenerativeSession, session_id)
            return {
                "prompt": prompt_result,
                "session_id": session_id,
                "parameters": session.parameters if session else None,
            }
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
            ) from e


@router.get("/", status_code=status.HTTP_200_OK)
async def get_all_prompts(
    session_factory: sessionmaker = Depends(lambda: di["session_factory"]),
):
    """Get all available RAG prompts."""

    component_registry = di["component_registry"]
    with session_factory() as db:
        service = PromptService(db, component_registry)
        return service.get_all()
