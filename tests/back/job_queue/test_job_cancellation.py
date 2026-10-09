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

import os
import sqlite3
import threading
import time
import uuid
from pathlib import Path
from types import SimpleNamespace

import pytest
from huey.signals import SIGNAL_ERROR, SIGNAL_EXECUTING
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from DashAI.back.dependencies.database.models import Base
from DashAI.back.dependencies.job_queues.base_job_queue import JobQueueError
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


class ThreadedJob(CancellableJob):
    """Job whose work runs in a non-daemon thread pool, like a model download.

    The main thread only waits on the pool, which is where a SIGTERM that is
    turned into SystemExit gets stuck until the pool finishes.
    """

    def run(self):
        from concurrent.futures import ThreadPoolExecutor

        with ThreadPoolExecutor(max_workers=1) as pool:
            pool.submit(time.sleep, self.SLEEP_SECONDS).result()
        return "completed"


class QuickJob(CancellableJob):
    """Same job, but it returns immediately."""

    SLEEP_SECONDS = 0

    def get_job_name(self) -> str:
        return "Quick Job"


class MarkingJob(CancellableJob):
    """Job that leaves marker files where its entity status would be written.

    Flags on the job object would not do: the cancel endpoint and the consumer
    each work on their own copy of the job, so the markers go to disk.
    """

    def _mark(self, name: str) -> None:
        Path(self.kwargs["marker_dir"], name).touch()

    def run(self):
        self._mark("ran")
        return super().run()

    def on_cancel(self) -> None:
        self._mark("cancel")

    def set_status_as_error(self) -> None:
        self._mark("error")


class QuickMarkingJob(MarkingJob):
    """Marking job that returns immediately."""

    SLEEP_SECONDS = 0


class CrashingJob(MarkingJob):
    """Marking job whose worker dies without anyone cancelling it."""

    def run(self):
        os._exit(3)


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


def _pid_alive(pid: int) -> bool:
    """Tell whether *pid* is a live, non-zombie process."""
    try:
        with open(f"/proc/{pid}/stat") as f:
            return f.read().rsplit(")", 1)[1].split()[0] != "Z"
    except FileNotFoundError:
        return False


@pytest.mark.skipif(
    not Path("/proc").is_dir(), reason="needs /proc and a POSIX shell wrapper"
)
def test_cancel_kills_the_worker_behind_a_launcher_wrapper(
    queue: HueyJobQueue, tmp_path: Path
):
    """A cancel must kill the interpreter even when sys.executable is a wrapper.

    Packaged builds (the python-appimage AppImage) can point sys.executable at
    a shell script that runs Python as a child without exec, so the spawned
    process handle is the shell, not the worker. Killing only the shell left
    the job running in an orphaned interpreter.
    """
    import multiprocessing.spawn
    import sys
    from multiprocessing import resource_tracker

    wrapper = tmp_path / "python-wrapper"
    wrapper.write_text(f'#!/bin/sh\n"{sys.executable}" "$@"\n')
    wrapper.chmod(0o755)
    # Start the shared resource tracker with the real interpreter first, or it
    # would also run behind the wrapper and hang the test session on exit.
    resource_tracker.ensure_running()
    previous = multiprocessing.spawn.get_executable()
    multiprocessing.spawn.set_executable(str(wrapper))
    try:
        huey_id = "job-wrapped"
        _register_started(queue, huey_id)
        consumer = _ConsumerThread(queue, CancellableJob(), huey_id)
        consumer.start()
        pid = _wait_for_worker_pid(queue, huey_id)
        assert pid != queue._worker_proc.pid, "the wrapper was not in between"

        assert queue.cancel(huey_id, reason="cancelled") is True
        consumer.join(timeout=CANCEL_TIMEOUT)

        assert isinstance(consumer.error, _JobCancelledError)
        assert not _pid_alive(pid), "the job kept running after the cancel"
    finally:
        multiprocessing.spawn.set_executable(previous)
        if queue._worker_pid and _pid_alive(queue._worker_pid):
            os.kill(queue._worker_pid, 9)


def test_cancel_kills_a_job_working_in_a_thread_pool(queue: HueyJobQueue):
    """A cancel must end the worker at once even when a thread does the work.

    With SIGTERM turned into SystemExit the interpreter waited for the pool to
    finish, so a download kept running until the 30 s SIGKILL escalation, and
    the cancel request hung for as long.
    """
    huey_id = "job-threaded"
    _register_started(queue, huey_id)
    consumer = _ConsumerThread(queue, ThreadedJob(), huey_id)
    consumer.start()
    pid = _wait_for_worker_pid(queue, huey_id)

    started = time.monotonic()
    assert queue.cancel(huey_id, reason="cancelled") is True
    elapsed = time.monotonic() - started
    consumer.join(timeout=CANCEL_TIMEOUT)

    assert elapsed < 10, f"the worker outlived the cancel for {elapsed:.0f} s"
    assert isinstance(consumer.error, _JobCancelledError)
    assert not _pid_alive(pid)


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


def _simulate_dequeue(queue: HueyJobQueue, huey_id: str, status: str) -> None:
    """Take the task out of the Huey table the way the consumer does."""
    with sqlite3.connect(queue.db_path) as conn:
        conn.execute("DELETE FROM task")
        conn.execute("UPDATE task_copy SET status = ? WHERE id = ?", (status, huey_id))


def test_cancel_running_job_marks_its_entity_as_error(
    queue: HueyJobQueue, tmp_path: Path
):
    """A killed job must leave its entity in error, whatever the entity is."""
    huey_id = "job-running-entity"
    _register_started(queue, huey_id)
    job = MarkingJob(marker_dir=str(tmp_path))

    consumer = _ConsumerThread(queue, job, huey_id)
    consumer.start()
    _wait_for_worker_pid(queue, huey_id)

    assert queue.cancel(huey_id) is True
    consumer.join(timeout=CANCEL_TIMEOUT)

    assert isinstance(consumer.error, _JobCancelledError)
    assert (tmp_path / "error").exists(), "the entity would stay 'started'"
    assert (tmp_path / "cancel").exists()


def test_cancel_of_a_dequeued_job_marks_the_entity_before_returning(
    queue: HueyJobQueue, tmp_path: Path
):
    """The entity must already be in error when the cancel request returns."""
    huey_id = queue.put(MarkingJob(marker_dir=str(tmp_path))).id
    _simulate_dequeue(queue, huey_id, "started")

    assert queue.cancel(huey_id) is True

    assert _column(queue, huey_id, "status") == "cancelled"
    assert (tmp_path / "error").exists()


def test_cancel_while_the_worker_spawns_stops_the_job(
    queue: HueyJobQueue, tmp_path: Path
):
    """A cancel landing before the PID is recorded must keep the job from running."""
    huey_id = "job-spawning"
    _register_started(queue, huey_id)

    assert queue.cancel(huey_id) is True
    assert _column(queue, huey_id, "status") == "cancelled"

    with pytest.raises(_JobCancelledError):
        queue._run_in_subprocess(QuickMarkingJob(marker_dir=str(tmp_path)), huey_id)

    assert not (tmp_path / "ran").exists(), "the cancelled job still ran"
    assert (tmp_path / "error").exists()
    assert _column(queue, huey_id, "pid") is None


def test_cancel_before_start_is_not_overwritten_by_the_start_signal(
    queue: HueyJobQueue, tmp_path: Path
):
    """A job cancelled between dequeue and start must never run."""
    huey_id = queue.put(QuickMarkingJob(marker_dir=str(tmp_path))).id
    _simulate_dequeue(queue, huey_id, "not_started")

    assert queue.cancel(huey_id) is True
    queue.huey._emit(SIGNAL_EXECUTING, SimpleNamespace(id=huey_id))
    assert _column(queue, huey_id, "status") == "cancelled"

    with pytest.raises(_JobCancelledError):
        queue._run_job(QuickMarkingJob(marker_dir=str(tmp_path)), huey_id)

    assert not (tmp_path / "ran").exists()
    assert (tmp_path / "error").exists()
    assert (tmp_path / "cancel").exists()


def test_cancel_queued_job_marks_the_entity_and_cleans_up(
    queue: HueyJobQueue, tmp_path: Path
):
    """A queued cancel must end like a running one: entity in error, cleaned up."""
    huey_id = queue.put(QuickMarkingJob(marker_dir=str(tmp_path))).id

    assert queue.cancel(huey_id) is True

    assert _column(queue, huey_id, "status") == "cancelled"
    assert (tmp_path / "error").exists()
    assert (tmp_path / "cancel").exists(), "partial artifacts would leak"


def test_worker_crash_marks_the_entity_as_error(queue: HueyJobQueue, tmp_path: Path):
    """A worker that dies on its own must also leave the entity in error."""
    huey_id = "job-crashing"
    _register_started(queue, huey_id)

    with pytest.raises(JobQueueError):
        queue._run_in_subprocess(CrashingJob(marker_dir=str(tmp_path)), huey_id)

    assert (tmp_path / "error").exists()


def test_error_signal_keeps_a_cancel_but_reports_the_change(queue: HueyJobQueue):
    """SIGNAL_ERROR after a cancel must keep the status and refresh last_update."""
    huey_id = "job-cancelled"
    with sqlite3.connect(queue.db_path) as conn:
        conn.execute(
            "INSERT INTO task_copy (id, task_type, job_name, status, last_update)"
            " VALUES (?, ?, ?, ?, ?)",
            (huey_id, "QuickJob", "Quick Job", "cancelled", "2000-01-01 00:00:00"),
        )

    queue.huey._emit(
        SIGNAL_ERROR, SimpleNamespace(id=huey_id), _JobCancelledError("cancelled")
    )

    assert _column(queue, huey_id, "status") == "cancelled"
    assert _column(queue, huey_id, "last_update") > "2000-01-01 00:00:00"


def test_consumer_does_not_mark_the_entity_again_after_the_cancel_did(
    queue: HueyJobQueue, tmp_path: Path
):
    """A late second mark would clobber a retry the user started meanwhile."""
    huey_id = queue.put(QuickMarkingJob(marker_dir=str(tmp_path))).id
    _simulate_dequeue(queue, huey_id, "started")

    assert queue.cancel(huey_id) is True
    assert (tmp_path / "error").exists()
    (tmp_path / "error").unlink()

    with pytest.raises(_JobCancelledError):
        queue._run_job(QuickMarkingJob(marker_dir=str(tmp_path)), huey_id)

    assert not (tmp_path / "error").exists()
    assert (tmp_path / "cancel").exists(), "the cleanup must still run"


def test_progress_does_not_surface_a_cancel(queue: HueyJobQueue):
    """A worker still reporting progress must not bump a cancelled row."""
    huey_id = "job-cancelled-progress"
    with sqlite3.connect(queue.db_path) as conn:
        conn.execute(
            "INSERT INTO task_copy (id, task_type, job_name, status, last_update)"
            " VALUES (?, ?, ?, ?, ?)",
            (huey_id, "QuickJob", "Quick Job", "cancelled", "2000-01-01 00:00:00"),
        )

    queue.report_progress(huey_id, 50.0, "halfway")

    assert _column(queue, huey_id, "last_update") == "2000-01-01 00:00:00"
    assert _column(queue, huey_id, "progress") is None


def test_restart_closes_jobs_left_started(queue: HueyJobQueue, tmp_path: Path):
    """A job that died with the previous consumer must not stay in progress."""
    huey_id = queue.put(MarkingJob(marker_dir=str(tmp_path))).id
    _simulate_dequeue(queue, huey_id, "started")

    assert queue.reconcile_interrupted_jobs() == 1

    assert _column(queue, huey_id, "status") == "killed"
    assert (tmp_path / "error").exists()
    assert queue.is_empty()
