"""Resolving and cancelling a RAG session's indexing job.

``GenerativeSession.index_job_id`` is only a pointer. The job queue's
``task_copy`` table is what actually knows whether that job is alive, so every
question about indexing state is answered by asking the queue, never by
trusting the column. That is what makes a stale pointer harmless: a job whose
worker was killed is flipped to ``killed`` by the queue's watchdog within
seconds, and stops looking live on its own.
"""

import logging
from typing import Any, Dict, Optional

from DashAI.back.dependencies.database.models import GenerativeSession
from DashAI.back.dependencies.job_queues.base_job_queue import (
    BaseJobQueue,
    JobQueueError,
)

log = logging.getLogger(__name__)

#: Queue states in which a job still has work left to do.
_LIVE_STATUSES = ("not_started", "started")


def get_index_job(
    session: GenerativeSession,
    job_queue: Optional[BaseJobQueue],
) -> Optional[Dict[str, Any]]:
    """Return the queue state of a session's indexing job, alive or not.

    Includes finished and failed jobs on purpose: a failed index has to stay
    visible after a page reload, and the queue row is the only place holding
    the error message.

    Parameters
    ----------
    session : GenerativeSession
        The session whose ``index_job_id`` should be resolved.
    job_queue : Optional[BaseJobQueue]
        The queue to ask. ``None`` disables resolution entirely, which is what
        callers that have no queue handy (most tests) want.

    Returns
    -------
    Optional[dict]
        The queue's status dict, or ``None`` when there is no job to resolve.
    """
    if job_queue is None or not session.index_job_id:
        return None
    try:
        return job_queue.status(session.index_job_id)
    except JobQueueError:
        # Dismissed from task_copy: the job is gone, and so is any record of it.
        return None
    except Exception:  # pragma: no cover - status must never break a read
        log.exception("Index job lookup failed for session %s", session.id)
        return None


def get_live_index_job(
    session: GenerativeSession,
    job_queue: Optional[BaseJobQueue],
) -> Optional[Dict[str, Any]]:
    """Return the session's indexing job only while it still has work to do."""
    state = get_index_job(session, job_queue)
    if state is None or state.get("status") not in _LIVE_STATUSES:
        return None
    return state


def cancel_live_index_job(
    session: GenerativeSession,
    job_queue: Optional[BaseJobQueue],
) -> bool:
    """Stop an in-flight index for a session whose inputs are about to change.

    Call this *before* mutating documents or parameters. Otherwise the request
    handler and the indexing worker race over the very same chunk, retriever
    and embedding rows — the cleanup deleting what the job is still writing.

    Clears ``index_job_id`` but does not commit; the caller's own transaction
    is what makes the change durable.

    Returns
    -------
    bool
        Whether a live job was found and cancelled.
    """
    if get_live_index_job(session, job_queue) is None:
        return False
    job_id = session.index_job_id
    try:
        job_queue.cancel(job_id, reason="cancelled")
    except Exception:  # pragma: no cover - a doomed job must not block the write
        log.exception("Could not cancel index job %s", job_id)
    session.index_job_id = None
    log.debug("Cancelled index job %s for session %s", job_id, session.id)
    return True
