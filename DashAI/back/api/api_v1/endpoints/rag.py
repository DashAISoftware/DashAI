"""RAG helper endpoints: presets, defaults, resolved configuration, index state.

Every response here is already localized and already resolved: the frontend
renders what it receives instead of keeping its own preset tables, default
values or class-name-to-label mappings.
"""

import logging
from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from kink import di

from DashAI.back.core.utils import localize
from DashAI.back.services.RAG.chunking_presets import (
    get_chunking_presets as resolve_chunking_presets,
)
from DashAI.back.services.RAG.index_status_service import IndexStatusService
from DashAI.back.services.RAG.retriever_presets import (
    get_retriever_presets as resolve_retriever_presets,
)
from DashAI.back.services.RAG.session_configuration_service import (
    SessionConfigurationService,
)
from DashAI.back.services.RAG.session_defaults_service import build_default_parameters

if TYPE_CHECKING:
    from sqlalchemy.orm import sessionmaker

    from DashAI.back.dependencies.registry import ComponentRegistry

router = APIRouter()
log = logging.getLogger(__name__)


@router.get("/retriever-presets")
def retriever_presets(
    top_k: int = Query(default=10, ge=1),
    accept_language: str | None = Header(default=None),
    component_registry: "ComponentRegistry" = Depends(lambda: di["component_registry"]),
):
    """Return resolved retriever preset recipes for the given top_k.

    Parameters
    ----------
    top_k : int
        Number of chunks to configure (>= 1). Defaults to 10.
    accept_language : str | None
        The 'Accept-Language' header, used to localize preset names.
    component_registry : ComponentRegistry
        Registry used to resolve each preset's schema defaults.

    Returns
    -------
    list[dict]
        One dict per preset: ``{key, display_name, description, component,
        params}``.
    """
    presets = resolve_retriever_presets(top_k, component_registry)
    return localize(presets, accept_language)


@router.get("/chunking-presets")
def chunking_presets(
    accept_language: str | None = Header(default=None),
    component_registry: "ComponentRegistry" = Depends(lambda: di["component_registry"]),
):
    """Return resolved chunking preset recipes.

    Parameters
    ----------
    accept_language : str | None
        The 'Accept-Language' header, used to localize preset names.
    component_registry : ComponentRegistry
        Registry used to resolve the chunker's schema defaults.

    Returns
    -------
    list[dict]
        One dict per preset: ``{key, display_name, description, component,
        params}``.
    """
    presets = resolve_chunking_presets(component_registry)
    return localize(presets, accept_language)


@router.get("/session-defaults")
def session_defaults(
    accept_language: str | None = Header(default=None),
    component_registry: "ComponentRegistry" = Depends(lambda: di["component_registry"]),
):
    """Return the configuration a new RAG session gets when the user picks none.

    Lets the creation form show what the defaults will be without recomputing
    them, and keeps that preview honest: it is the very same dict the backend
    applies on create.

    Parameters
    ----------
    accept_language : str | None
        The 'Accept-Language' header, used to pick the prompt language.
    component_registry : ComponentRegistry
        Registry used to resolve schema placeholders.

    Returns
    -------
    dict
        ``{chunking_model, retriever_model, prompt}``, each a resolved
        ``{component, params, display_name}`` reference.
    """
    defaults = build_default_parameters(component_registry, accept_language)
    for ref in defaults.values():
        component = ref["component"]
        display_name = component
        if component in component_registry:
            display_name = component_registry[component]["display_name"] or component
        ref["display_name"] = display_name
    return localize(defaults, accept_language)


@router.get("/sessions/{session_id}/configuration")
def session_configuration(
    session_id: int,
    accept_language: str | None = Header(default=None),
    session_factory: "sessionmaker" = Depends(lambda: di["session_factory"]),
    component_registry: "ComponentRegistry" = Depends(lambda: di["component_registry"]),
):
    """Return a RAG session's configuration in the UI's own vocabulary.

    Parameters
    ----------
    session_id : int
        The RAG session to describe.
    accept_language : str | None
        The 'Accept-Language' header, used to localize every label.
    session_factory : Callable[..., ContextManager[Session]]
        Factory for the SQLAlchemy session.
    component_registry : ComponentRegistry
        Registry providing display names, descriptions and schemas.

    Returns
    -------
    dict
        One section per RAG component plus ``context_budget``.

    Raises
    ------
    HTTPException
        404 if the session does not exist.
    """
    with session_factory() as db:
        try:
            configuration = SessionConfigurationService(
                db, component_registry
            ).get_configuration(session_id)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
            ) from e
    return localize(configuration, accept_language)


@router.get("/sessions/{session_id}/index-status")
def session_index_status(
    session_id: int,
    accept_language: str | None = Header(default=None),
    session_factory: "sessionmaker" = Depends(lambda: di["session_factory"]),
    component_registry: "ComponentRegistry" = Depends(lambda: di["component_registry"]),
):
    """Report whether a RAG session's documents are already indexed.

    Read-only: indexing itself still happens inside the chat job, so this never
    triggers work, it only reports what the job would find.

    Parameters
    ----------
    session_id : int
        The RAG session to inspect.
    accept_language : str | None
        The 'Accept-Language' header, used to localize the status message.
    session_factory : Callable[..., ContextManager[Session]]
        Factory for the SQLAlchemy session.
    component_registry : ComponentRegistry
        Registry used to resolve retriever kinds.

    Returns
    -------
    dict
        ``{status, chunk_set_id, total_chunks, retriever_ready, documents,
        message}``.

    Raises
    ------
    HTTPException
        404 if the session does not exist.
    """
    with session_factory() as db:
        try:
            state = IndexStatusService(db, component_registry).get_status(session_id)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
            ) from e
    return localize(state, accept_language)
