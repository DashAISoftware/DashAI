"""Cancellation tests that drive the real spawned worker process.

These deliberately avoid the ``test_job_queue`` fixture. That one puts Huey in
immediate mode, where jobs run inline in the calling thread and there is no
worker subprocess to cancel, so it cannot reach any of this code. Each test
here builds its own ``HueyJobQueue`` against a temporary database and lets the
persistent worker be spawned, killed and respawned for real.

Spawning the worker costs about two seconds because the child rebuilds the
dependency injection container from scratch, so this module runs in seconds
rather than milliseconds. That is the price of covering the one path that
cannot be exercised in-process.
"""

import sqlite3
import threading
import time
import uuid

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from DashAI.back.dependencies.database.models import Base
from DashAI.back.dependencies.job_queues.huey_job_queue import (
    HueyJobQueue,
    _JobCancelledError,
)
from DashAI.back.job.base_job import BaseJob

# Generous: a cold worker has to import the whole component registry.
WORKER_TIMEOUT = 120
# A kill lands in well under a second, so a regression here should fail fast
# instead of blocking until the job's own sleep runs out.
CANCEL_TIMEOUT = 30


class CancellableJob(BaseJob):
    """Job that blocks until something kills the worker running it.

    Declared at module level on purpose: dill has to rebuild the class inside
    the spawned worker, and a class defined inside a test function does not
    survive that round trip.
    """

    SLEEP_SECONDS = 120

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.cancel_hook_ran = False

    def run(self):
        time.sleep(self.SLEEP_SECONDS)
        return "completed"

    def on_cancel(self) -> None:
        self.cancel_hook_ran = True

    def set_status_as_delivered(self) -> None:
        return None

    def set_status_as_error(self) -> None:
        return None

    def get_job_name(self) -> str:
        return "Cancellable Job"


class QuickJob(CancellableJob):
    """Same job, but it returns immediately."""

    SLEEP_SECONDS = 0

    def get_job_name(self) -> str:
        return "Quick Job"


@pytest.fixture(name="di_session_factory")
def fixture_di_session_factory():
    """Register a throwaway session factory in the container.

    After a cancel the queue marks the job's database entity as errored. With
    no session factory registered that call logs an exception instead of
    running, which would bury a real failure under a noisy traceback. Whatever
    was registered before is restored so the rest of the suite is unaffected.
    """
    from kink import di

    # kink's Container has no .get(), so this cannot be a one-liner.
    previous = None
    if "session_factory" in di:
        previous = di["session_factory"]
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    di["session_factory"] = sessionmaker(bind=engine)

    yield

    if previous is None:
        del di["session_factory"]
    else:
        di["session_factory"] = previous


@pytest.fixture(name="queue")
def fixture_queue(tmp_path, di_session_factory):
    """A real, non-immediate queue whose worker is always cleaned up."""
    queue = HueyJobQueue(f"cancel_{uuid.uuid4().hex}", path_db=str(tmp_path))

    yield queue

    proc = queue._worker_proc
    if proc is not None and proc.is_alive():
        proc.terminate()
        proc.join(timeout=30)


def _register_started(queue: HueyJobQueue, huey_id: str) -> None:
    """Insert the task_copy row the consumer writes before running a job."""
    with sqlite3.connect(queue.db_path) as conn:
        conn.execute(
            "INSERT INTO task_copy (id, task_type, job_name, status)"
            " VALUES (?, ?, ?, ?)",
            (huey_id, "CancellableJob", "Cancellable Job", "started"),
        )


def _column(queue: HueyJobQueue, huey_id: str, name: str):
    """Read one task_copy column, or None when the row is gone."""
    with sqlite3.connect(queue.db_path) as conn:
        row = conn.execute(
            f"SELECT {name} FROM task_copy WHERE id = ?", (huey_id,)
        ).fetchone()
    return row[0] if row else None


def _wait_for_worker_pid(queue: HueyJobQueue, huey_id: str) -> int:
    """Block until the job is really executing inside the worker.

    Waiting for the recorded PID instead of sleeping a fixed amount is what
    keeps these tests deterministic: the queue writes it only once the job has
    been handed to a live worker process.
    """
    deadline = time.monotonic() + WORKER_TIMEOUT
    while time.monotonic() < deadline:
        pid = _column(queue, huey_id, "pid")
        if pid:
            return int(pid)
        time.sleep(0.05)
    raise AssertionError(f"the worker never picked up job {huey_id}")


class _ConsumerThread(threading.Thread):
    """Run a job through the worker the way the Huey consumer does."""

    def __init__(self, queue: HueyJobQueue, job: BaseJob, huey_id: str):
        super().__init__(daemon=True)
        self.queue = queue
        self.job = job
        self.huey_id = huey_id
        self.result = None
        self.error = None

    def run(self) -> None:
        try:
            self.result = self.queue._run_in_subprocess(self.job, self.huey_id)
        except BaseException as error:  # noqa: BLE001 - re-raised by the test
            self.error = error


def test_cancel_running_job_kills_the_worker(queue: HueyJobQueue):
    """Cancelling a started job must kill its worker and stick as 'cancelled'."""
    huey_id = "job-running"
    _register_started(queue, huey_id)
    job = CancellableJob()

    consumer = _ConsumerThread(queue, job, huey_id)
    consumer.start()
    pid = _wait_for_worker_pid(queue, huey_id)
    assert pid == queue._worker_proc.pid

    assert queue.cancel(huey_id, reason="cancelled") is True

    consumer.join(timeout=CANCEL_TIMEOUT)
    assert not consumer.is_alive(), "the consumer never noticed the kill"

    # The consumer must raise so Huey fires SIGNAL_ERROR, and the on_error
    # guard is what keeps the terminal status from being overwritten.
    assert isinstance(consumer.error, _JobCancelledError)
    assert _column(queue, huey_id, "status") == "cancelled"
    assert _column(queue, huey_id, "pid") is None
    assert not queue._worker_proc.is_alive()
    assert job.cancel_hook_ran, "on_cancel() never ran, partial artifacts would leak"


def test_cancel_queued_job_removes_it_from_the_task_table(queue: HueyJobQueue):
    """A job that never started must leave the Huey queue, not just task_copy."""
    task = queue.put(QuickJob())
    huey_id = task.id
    assert _column(queue, huey_id, "status") == "not_started"

    with sqlite3.connect(queue.db_path) as conn:
        pending = conn.execute("SELECT COUNT(*) FROM task").fetchone()[0]
    assert pending == 1

    assert queue.cancel(huey_id) is True

    assert _column(queue, huey_id, "status") == "cancelled"
    with sqlite3.connect(queue.db_path) as conn:
        pending = conn.execute("SELECT COUNT(*) FROM task").fetchone()[0]
    assert pending == 0, "the task would still run when a consumer starts"


@pytest.mark.parametrize("status", ["finished", "error", "cancelled", "killed"])
def test_cancel_on_a_terminal_job_dismisses_it(queue: HueyJobQueue, status: str):
    """On a terminal job the same endpoint means 'dismiss', not 'cancel'."""
    huey_id = f"job-{status}"
    with sqlite3.connect(queue.db_path) as conn:
        conn.execute(
            "INSERT INTO task_copy (id, task_type, job_name, status)"
            " VALUES (?, ?, ?, ?)",
            (huey_id, "QuickJob", "Quick Job", status),
        )

    assert queue.cancel(huey_id) is True
    assert _column(queue, huey_id, "status") is None, "the row should be gone"


def test_cancel_on_an_unknown_job_reports_failure(queue: HueyJobQueue):
    """An id nobody knows must return False so the API can answer 404."""
    assert queue.cancel("does-not-exist") is False


def test_worker_respawns_after_a_cancel(queue: HueyJobQueue):
    """The queue must survive a kill: the next job gets a fresh worker."""
    huey_id = "job-to-kill"
    _register_started(queue, huey_id)

    consumer = _ConsumerThread(queue, CancellableJob(), huey_id)
    consumer.start()
    killed_pid = _wait_for_worker_pid(queue, huey_id)
    queue.cancel(huey_id, reason="killed")
    consumer.join(timeout=CANCEL_TIMEOUT)

    next_id = "job-after-kill"
    _register_started(queue, next_id)
    result = queue._run_in_subprocess(QuickJob(), next_id)

    assert result == "completed"
    assert queue._worker_proc.is_alive()
    assert queue._worker_proc.pid != killed_pid, "the dead worker was reused"
