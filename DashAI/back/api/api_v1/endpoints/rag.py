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
from DashAI.back.dependencies.database.models import GenerativeSession
from DashAI.back.job.RAG_index_job import RAGIndexJob
from DashAI.back.models.RAG.RAG_constants import RAG_PARAM_KEYS
from DashAI.back.services.RAG.chunking_presets import (
    get_chunking_presets as resolve_chunking_presets,
)
from DashAI.back.services.RAG.index_status_service import (
    STATUS_INDEXED,
    STATUS_INDEXING,
    STATUS_NO_DOCUMENTS,
    IndexStatusService,
)
from DashAI.back.services.RAG.retriever_presets import (
    get_retriever_presets as resolve_retriever_presets,
)
from DashAI.back.services.RAG.session_configuration_service import (
    SessionConfigurationService,
)
from DashAI.back.services.RAG.session_defaults_service import build_default_parameters

if TYPE_CHECKING:
    from sqlalchemy.orm import sessionmaker

    from DashAI.back.dependencies.job_queues.base_job_queue import BaseJobQueue
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
    job_queue: "BaseJobQueue" = Depends(lambda: di["job_queue"]),
):
    """Report whether a RAG session's documents are already indexed.

    Read-only: it never chunks, embeds or enqueues, so it is safe to poll while
    an indexing job runs.

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
    job_queue : BaseJobQueue
        Queue consulted for a running indexing job.

    Returns
    -------
    dict
        ``{status, chunk_set_id, total_chunks, retriever_ready, documents,
        message, job_id, job}``.

    Raises
    ------
    HTTPException
        404 if the session does not exist.
    """
    with session_factory() as db:
        try:
            state = IndexStatusService(db, component_registry, job_queue).get_status(
                session_id
            )
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
            ) from e
    return localize(state, accept_language)


@router.post("/sessions/{session_id}/index", status_code=status.HTTP_202_ACCEPTED)
def start_session_indexing(
    session_id: int,
    accept_language: str | None = Header(default=None),
    session_factory: "sessionmaker" = Depends(lambda: di["session_factory"]),
    component_registry: "ComponentRegistry" = Depends(lambda: di["component_registry"]),
    job_queue: "BaseJobQueue" = Depends(lambda: di["job_queue"]),
):
    """Index a session's documents now, if they are not already.

    Idempotent and coalescing: nothing to index, already indexed, and already
    indexing all return the current state without enqueueing anything. That is
    what lets callers fire this after *every* save without deciding for
    themselves which settings invalidate the index — the chunk-set signature
    already owns that rule, and a second opinion could only drift from it.

    Returns the same payload as ``/index-status`` so no follow-up GET is needed.

    Parameters
    ----------
    session_id : int
        The RAG session to index.
    accept_language : str | None
        The 'Accept-Language' header, used to localize the status message.
    session_factory : Callable[..., ContextManager[Session]]
        Factory for the SQLAlchemy session.
    component_registry : ComponentRegistry
        Registry used to resolve retriever kinds.
    job_queue : BaseJobQueue
        Queue the indexing job is submitted to.

    Returns
    -------
    dict
        The session's index status, as ``/index-status`` reports it.

    Raises
    ------
    HTTPException
        404 if the session does not exist, 409 if its parameters do not
        describe a complete pipeline.
    """
    with session_factory() as db:
        service = IndexStatusService(db, component_registry, job_queue)
        try:
            state = service.get_status(session_id)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
            ) from e

        if state["status"] in (STATUS_NO_DOCUMENTS, STATUS_INDEXED, STATUS_INDEXING):
            return localize(state, accept_language)

        session = db.get(GenerativeSession, session_id)
        missing = RAG_PARAM_KEYS - set(session.parameters or {})
        if missing:
            # Unreachable for sessions created through the API, which always
            # get every key; a legacy row would otherwise fail deep inside the
            # job with a far less useful message.
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    f"Session {session_id} is missing configuration: {sorted(missing)}."
                ),
            )

        job = RAGIndexJob(session_id=session_id)
        job.set_status_as_delivered()
        session.index_job_id = str(job_queue.put(job).id)
        db.commit()

        return localize(service.get_status(session_id), accept_language)
