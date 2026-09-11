"""Filesystem removals that wait for the database transaction to commit.

Deleting a file or a directory cannot be rolled back, so doing it while a
transaction is still open couples two things that can disagree: if the
transaction then fails, the rows survive and point at something that is gone.
Doing it after the commit by hand works, but only for as long as every call
site remembers to -- and that has now been the source of the same bug three
times over.

Registering the removal against the session instead makes the ordering a
property of the transaction rather than of the caller's discipline: the paths
are removed when (and only when) the session that queued them commits, and are
dropped on rollback.

    remove_after_commit(db, blob_path)
    db.delete(document)
    db.commit()            # the file goes here, not before

A session may commit many times over its life -- a job doing several
operations, say. Each commit takes only what was queued since the last one,
because the queue lives in ``Session.info`` and is drained as it is read.

Savepoints need more care than they first appear to. ``after_commit`` fires
when a savepoint is *released*, and both ``after_rollback`` and
``after_soft_rollback`` fire when one is rolled back -- so none of the three
means "the work is durable" on its own. What does is the end of the
transaction with no parent: it happens exactly once per real transaction, and
is preceded by ``after_commit`` only if that transaction committed.
"""

import logging
import os
import shutil
from typing import List, Optional

from sqlalchemy import event
from sqlalchemy.orm import Session

log = logging.getLogger(__name__)

#: Key under which pending paths live in ``Session.info``.
_PENDING_KEY = "dashai_pending_path_removals"
#: Set between a commit and the end of the transaction it belonged to.
_COMMITTED_KEY = "dashai_transaction_committed"


def remove_after_commit(db: Session, path: Optional[str]) -> None:
    """Queue a filesystem path for removal once ``db`` commits.

    Parameters
    ----------
    db : Session
        The session whose commit should trigger the removal.
    path : str | None
        A file or directory. ``None`` and empty paths are ignored, so callers
        do not have to guard a nullable column.
    """
    if not path:
        return
    db.info.setdefault(_PENDING_KEY, []).append(path)


def remove_now(path: Optional[str]) -> None:
    """Remove a file or directory immediately, warning if it cannot be removed.

    Prefer :func:`remove_after_commit`. This exists for paths that are not tied
    to a transaction at all.

    Parameters
    ----------
    path : str | None
    """
    if not path:
        return
    try:
        if os.path.isdir(path):
            shutil.rmtree(path)
        elif os.path.exists(path):
            os.remove(path)
    except OSError as exc:
        log.warning("Failed to remove %s: %s", path, exc)


def _take_pending(session: Session) -> List[str]:
    """Remove and return the paths queued against a session."""
    return session.info.pop(_PENDING_KEY, [])


@event.listens_for(Session, "after_commit")
def _mark_committed(session: Session) -> None:
    """Note that a commit happened; which commit is settled below.

    This fires for a savepoint release as well as for the real thing, so it
    cannot act on its own.
    """
    session.info[_COMMITTED_KEY] = True


@event.listens_for(Session, "after_transaction_end")
def _settle_pending_paths(session: Session, transaction: object) -> None:
    """Remove or discard the queued paths once the real transaction ends.

    ``after_commit`` and ``after_rollback`` both fire for savepoints, so neither
    can be trusted to mean "the work is durable". The transaction that has no
    parent is the outermost one, and it ends exactly once -- preceded by
    ``after_commit`` if it committed, and not if it rolled back. That is the
    only moment at which removing a file is safe.
    """
    if getattr(transaction, "parent", None) is not None:
        # An inner transaction or a savepoint ended. Releasing a savepoint is
        # not a commit, so drop the mark it may have just left.
        session.info.pop(_COMMITTED_KEY, None)
        return

    committed = session.info.pop(_COMMITTED_KEY, False)
    pending = _take_pending(session)
    if not committed:
        return
    for path in pending:
        remove_now(path)
