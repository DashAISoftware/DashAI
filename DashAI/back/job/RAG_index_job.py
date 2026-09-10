"""Eager indexing of a RAG session's documents.

The chat job indexes lazily, as a side effect of answering the first message,
which makes that message pay for the whole chunking and embedding run. This job
does the same work up front — when a document is uploaded, or when a
configuration change invalidates the index — so the chat stays fast and the
progress is something the user can actually watch.
"""

import gc
import logging
from typing import Dict

from kink import di, inject

from DashAI.back.dependencies.database.models import GenerativeSession
from DashAI.back.job.base_job import BaseJob, JobError
from DashAI.back.models.RAG.RAG_constants import RAG_PARAM_KEYS as _RAG_PARAM_KEYS
from DashAI.back.models.RAG.RAG_pipeline import RAGPipelineConfig
from DashAI.back.services.RAG.setup_service import SetupService

log = logging.getLogger(__name__)


class RAGIndexJob(BaseJob):
    """Chunks, embeds and fits the retriever for one RAG session.

    Deliberately never builds the generation model: indexing must not load LLM
    weights it will not use. See :meth:`SetupService.build_index`.

    ``ISOLATED`` stays True (the default): this loads embedding models, and the
    subprocess boundary is what frees their memory once the job is done.
    """

    def set_status_as_delivered(self) -> None:
        """Required by :class:`BaseJob`, but nothing calls it for this job.

        The hook exists to move a job's own DB entity into "delivered".
        Indexing has no entity — the index *is* the chunk and retriever rows —
        so there is nothing to move, and the endpoint does not call it.
        """
        log.debug("Index job delivered for session %s", self.kwargs.get("session_id"))

    def set_status_as_error(self) -> None:
        """Record failure. Unlike the delivered hook, the queue really does
        call this (on cancel, kill and delete), so it must never raise. There
        is no status column to write: the queue keeps the error message in
        ``task_copy``, which is what the index-status endpoint reports back.
        """
        log.debug("Index job failed for session %s", self.kwargs.get("session_id"))

    def get_job_name(self) -> str:
        """Get a descriptive name for the job."""
        session_id = self.kwargs.get("session_id")
        if not session_id:
            return "Indexing documents"

        try:
            with di["session_factory"]() as db:
                session = db.get(GenerativeSession, session_id)
                if session and session.name:
                    return f"Indexing: {session.name}"
        except Exception as e:
            log.exception(f"Error getting job name: {e}")

        return f"Indexing session #{session_id}"

    @inject
    def run(self) -> Dict[str, int]:
        """Build the session's index, reporting progress as it goes.

        Returns:
            ``{"chunk_set_id": int, "total_chunks": int}``, which the queue
            stores as the task result. Callers read the index through
            ``IndexStatusService`` instead; this is for the job log.

        Raises:
            JobError: If the session is missing, holds no documents, or its
                parameters do not describe a complete pipeline.
        """
        component_registry = di["component_registry"]
        session_factory = di["session_factory"]
        config = di["config"]

        if "session_id" not in self.kwargs:
            raise JobError("RAGIndexJob requires 'session_id' in kwargs.")

        session_id: int = self.kwargs["session_id"]

        try:
            with session_factory() as db:
                session = db.get(GenerativeSession, session_id)
                if not session:
                    raise JobError(f"Session {session_id} not found in DB.")

                # Whitelist-only, same as RAGJob: session parameters may carry
                # keys the pipeline config would reject.
                raw_params = dict(session.parameters or {})
                clean_params = {
                    k: v for k, v in raw_params.items() if k in _RAG_PARAM_KEYS
                }
                if not (clean_params.get("documents") or []):
                    raise JobError(f"Session {session_id} has no documents to index.")

                pipeline_config = RAGPipelineConfig.from_kwargs(
                    db=db,
                    component_registry=component_registry,
                    session_id=session_id,
                    env_RAG_path=config["RAG_PATH"],
                    **clean_params,
                )
                setup_service = SetupService(
                    db,
                    component_registry,
                    config["RAG_PATH"],
                )
                result = setup_service.build_index(
                    pipeline_config,
                    progress=self.report_progress,
                )
                log.debug(
                    "Indexed session %d: chunk set %d, %d chunks",
                    session_id,
                    result.chunk_set_id,
                    result.total_chunks,
                )
                return {
                    "chunk_set_id": result.chunk_set_id,
                    "total_chunks": result.total_chunks,
                }
        except JobError:
            self.set_status_as_error()
            raise
        except Exception as e:
            log.exception(e)
            self.set_status_as_error()
            raise JobError(f"Error indexing session {session_id}.") from e
        finally:
            import torch

            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            gc.collect()
