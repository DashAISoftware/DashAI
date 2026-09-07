import asyncio
import logging
import multiprocessing
import os
import signal
import sqlite3
import sys
import threading
import time
import warnings
from contextlib import suppress
from datetime import datetime, timezone
from pathlib import Path

import dill
from huey import SqliteHuey
from huey.serializer import Serializer as BaseSerializer
from huey.signals import (
    SIGNAL_COMPLETE,
    SIGNAL_ENQUEUED,
    SIGNAL_ERROR,
    SIGNAL_EXECUTING,
)

from DashAI.back.dependencies.job_queues.base_job_queue import (
    BaseJobQueue,
    JobQueueError,
)
from DashAI.back.job.base_job import BaseJob

warnings.filterwarnings(
    "ignore",
    message=".*mediapipe.*",
    category=UserWarning,
    module="controlnet_aux",
)
warnings.filterwarnings(
    "ignore",
    message=".*Importing from timm.models.layers.*",
    category=FutureWarning,
)
warnings.filterwarnings(
    "ignore",
    message=".*Importing from timm.models.registry.*",
    category=FutureWarning,
)
warnings.filterwarnings(
    "ignore",
    message=".*Overwriting tiny_vit.*",
    category=UserWarning,
    module="controlnet_aux",
)
warnings.filterwarnings(
    "ignore",
    message=".*found in sys.modules after import.*",
    category=RuntimeWarning,
)

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)


class _JobCancelledError(Exception):
    """Raised in the consumer when a job was intentionally cancelled/killed."""


def _worker_loop(in_q, out_q) -> None:
    """Persistent worker process.  Rebuilds the DI container once at startup,
    then loops accepting serialised jobs from *in_q* and writing results to *out_q*.

    Lifecycle:
    - After DI init: put ``{"ready": True}`` on out_q so the parent knows it's safe
      to send jobs.
    - Per job: get job_bytes from in_q → run → put outcome on out_q.  Job errors do
      NOT kill the loop; the worker survives and accepts the next job.
    - Shutdown: put ``None`` on in_q (sentinel) or kill the process externally.
    """
    import os as _os
    import signal as _signal
    import sys as _sys

    import dill as _dill

    # Rebuild DI container — spawn starts with no inherited state
    try:
        from pathlib import Path as _Path

        from DashAI.back.container import build_container
        from DashAI.back.dependencies.config_builder import build_config_dict

        _lp_env = _os.environ.get("DASHAI_LOCAL_PATH")
        _lp = (
            _Path(_os.path.expanduser(_lp_env)) if _lp_env else _Path.home() / ".DashAI"
        )
        _logging_level = _os.environ.get("DASHAI_LOGGING_LEVEL", "INFO")
        _config = build_config_dict(local_path=_lp, logging_level=_logging_level)
        build_container(_config)
    except Exception as _e:
        out_q.put(_dill.dumps({"ready": False, "exc": str(_e)}))
        return

    # Signal to the parent that we are ready to accept jobs
    out_q.put(_dill.dumps({"ready": True}))

    # Install SIGTERM handler on POSIX so the process exits cleanly when killed
    if _sys.platform != "win32":

        def _sigterm_handler(signum, frame):
            _sys.exit(0)

        _signal.signal(_signal.SIGTERM, _sigterm_handler)

    # Job loop — one blocking iteration per job
    while True:
        try:
            job_bytes = in_q.get()
        except (EOFError, OSError):
            break  # Parent closed the queue — shut down

        if job_bytes is None:
            break  # Explicit shutdown sentinel

        try:
            job = _dill.loads(job_bytes)
            result = job.run()
            out_q.put(_dill.dumps({"ok": True, "result": result}))
        except SystemExit:
            # SIGTERM handler raised SystemExit — exit without putting a result so
            # the parent detects the kill via proc.is_alive() == False.
            break
        except Exception as _exc:
            # Job-level errors are returned to the parent; the worker stays alive.
            # Guard against non-serialisable exceptions (e.g. SQLAlchemy errors
            # wrapping live connections) — fall back to a plain RuntimeError so
            # the dill.dumps call here never itself raises and kills the loop.
            try:
                _payload = _dill.dumps({"ok": False, "exc": _exc})
            except Exception:
                _payload = _dill.dumps({"ok": False, "exc": RuntimeError(str(_exc))})
            out_q.put(_payload)


def _terminate_pid(pid: int, grace_seconds: int = 30) -> None:
    """Terminate a process by PID, escalating to SIGKILL after grace_seconds.

    On Windows, os.kill sends TerminateProcess (immediate); grace_seconds ignored.
    """
    try:
        if sys.platform == "win32":
            os.kill(pid, signal.SIGTERM)  # == TerminateProcess on Windows
            return
        # POSIX: SIGTERM then wait, escalate to SIGKILL if needed
        try:
            os.kill(pid, signal.SIGTERM)
        except ProcessLookupError:
            return  # Already gone
        deadline = time.monotonic() + grace_seconds
        while time.monotonic() < deadline:
            try:
                os.kill(pid, 0)  # Probe — raises ProcessLookupError if dead
            except ProcessLookupError:
                return
            time.sleep(0.5)
        with suppress(ProcessLookupError):
            os.kill(pid, signal.SIGKILL)
    except ProcessLookupError:
        pass


class DillSerializer(BaseSerializer):
    def _serialize(self, data):
        return dill.dumps(data)

    def _deserialize(self, blob):
        return dill.loads(blob)


class HueyJobQueue(BaseJobQueue):
    """JobQueue implementation using Huey+SQLite."""

    def __init__(self, queue_name: str, path_db: str):
        self.db_path = Path(path_db) / (queue_name.strip() + ".db")
        self.serializer = DillSerializer()
        self.huey = SqliteHuey(
            name=queue_name,
            filename=self.db_path,
            serializer=self.serializer,
            immediate=False,
            immediate_use_memory=False,
        )
        self._enable_wal()
        self._ensure_task_copy_table()
        self._ensure_progress_columns()
        self._register_signals()

        # Persistent worker process state (None until first job or explicit pre-warm)
        self._worker_proc = None
        self._worker_in_q = None
        self._worker_out_q = None

        @self.huey.task(context=True, priority=0)
        def _execute_base_job(job: BaseJob, task=None):
            job.kwargs["huey_id"] = task.id
            # Run inline for test/immediate mode and for opt-out jobs (ISOLATED=False)
            if self.huey.immediate or not getattr(job, "ISOLATED", True):
                result = job.run()
                # Wrap coroutines produced by async run() methods (e.g. PipelineJob)
                if asyncio.iscoroutine(result):
                    result = asyncio.get_event_loop().run_until_complete(result)
                # If the job mutated the consumer's ComponentRegistry (e.g.
                # SyncComponentsJob), the worker's DI container is now stale.
                # Terminate it so _ensure_worker respawns a fresh one (fix #7).
                if getattr(job, "RESETS_WORKER", False):
                    with suppress(Exception):
                        if self._worker_proc is not None:
                            self._worker_proc.terminate()
                return result
            return self._run_in_subprocess(job, task.id)

        self._execute = _execute_base_job

    def _ensure_worker(self) -> None:
        """Ensure the persistent worker process is alive, spawning one if needed.

        The worker initialises the DI container once and then loops, accepting
        serialised jobs via ``_worker_in_q``.  If it has died (crash or cancel),
        new queues and a new process are created.

        Blocks until the worker signals readiness (DI container built).
        Raises ``JobQueueError`` if the worker fails to start within 120 s.
        """
        if self._worker_proc is not None and self._worker_proc.is_alive():
            return

        ctx = multiprocessing.get_context("spawn")
        self._worker_in_q = ctx.SimpleQueue()
        self._worker_out_q = ctx.Queue()
        proc = ctx.Process(
            target=_worker_loop,
            args=(self._worker_in_q, self._worker_out_q),
            daemon=True,
        )
        proc.start()
        self._worker_proc = proc

        # Wait for the worker to finish building its DI container
        import queue as _q

        try:
            msg_bytes = self._worker_out_q.get(timeout=120)
            msg = dill.loads(msg_bytes)
        except _q.Empty:
            proc.terminate()
            raise JobQueueError(
                "Worker process did not become ready within 120 s"
            ) from None
        except Exception as e:
            proc.terminate()
            raise JobQueueError(f"Worker ready-check failed: {e}") from e

        if not msg.get("ready"):
            proc.terminate()
            raise JobQueueError(
                f"Worker failed to initialise: {msg.get('exc', 'unknown error')}"
            )

        log.info("Persistent worker ready (PID %d)", proc.pid)

    def _run_in_subprocess(self, job: BaseJob, huey_id: str):
        """Run *job* in the persistent worker process and return its result.

        The worker is started once and reused across jobs.  If it was killed
        (by a cancel or a crash), ``_ensure_worker`` transparently spawns a
        replacement before the next job runs.

        If the worker is killed while a job is running, ``_JobCancelled`` is raised
        so that Huey fires SIGNAL_ERROR while the on_error guard keeps the terminal
        status (cancelled/killed) intact.
        """
        import queue as _q

        self._ensure_worker()

        try:
            job_bytes = dill.dumps(job)
        except Exception as e:
            raise JobQueueError(f"Failed to serialise job for subprocess: {e}") from e

        # Capture local references so a concurrent _ensure_worker respawn cannot
        # swap the queue objects underneath us mid-job.
        proc = self._worker_proc
        in_q = self._worker_in_q
        out_q = self._worker_out_q

        # Record PID so the cancel endpoint can kill the right process
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    "UPDATE task_copy SET pid=? WHERE id=?",
                    (proc.pid, huey_id),
                )
        except Exception:
            pass

        # Send the job to the worker
        in_q.put(job_bytes)

        # Poll for result; detect external kill via proc.is_alive()
        result_bytes = None
        killed_externally = False
        while True:
            try:
                result_bytes = out_q.get(timeout=0.5)
                break
            except _q.Empty:
                if not proc.is_alive():
                    # Worker died — do one final drain before declaring killed.
                    # Closes the race where the result landed on the queue in
                    # the same window as the external kill.
                    try:
                        result_bytes = out_q.get(timeout=0.1)
                    except _q.Empty:
                        killed_externally = True
                    break

        # Clear PID now that the job is done (or killed)
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("UPDATE task_copy SET pid=NULL WHERE id=?", (huey_id,))
        except Exception:
            pass

        if killed_externally:
            current_status = ""
            with suppress(Exception):
                current_status = self.status(huey_id)["status"]
            if current_status in ("cancelled", "killed"):
                with suppress(Exception):
                    job.on_cancel()
                self._mark_entity_error(huey_id)
                raise _JobCancelledError(f"Job {huey_id} was {current_status}")
            raise JobQueueError(
                f"Worker process exited unexpectedly (code {proc.exitcode})"
            )

        try:
            outcome = dill.loads(result_bytes)
        except Exception as e:
            raise JobQueueError(f"Failed to deserialise worker result: {e}") from e

        if outcome.get("ok"):
            return outcome.get("result")
        raise outcome.get("exc", JobQueueError("Unknown worker error"))

    @staticmethod
    def _mark_entity_error(huey_id: str) -> None:
        """Set the DB entity associated with *huey_id* to error status.

        Called from the consumer process after the worker subprocess is killed,
        because the job's own error-handling code never runs in that case.
        Failures are logged but never re-raised — entity marking is best-effort.
        """
        try:
            from kink import di

            from DashAI.back.dependencies.database.models import (
                Converter,
                Dataset,
                Explorer,
                GlobalExplainer,
                LocalExplainer,
                Run,
            )

            session_factory = di["session_factory"]
            with session_factory() as db:
                for model_cls in (
                    Run,
                    Dataset,
                    Explorer,
                    GlobalExplainer,
                    LocalExplainer,
                    Converter,
                ):
                    entity = (
                        db.query(model_cls).filter(model_cls.huey_id == huey_id).first()
                    )
                    if entity is not None:
                        entity.set_status_as_error()
                        db.commit()
                        return
        except Exception:
            log.exception(f"Could not mark entity error for huey_id={huey_id}")

    def set_test_mode(self, immediate: bool) -> None:
        """
        Set the immediate mode of the Huey job queue for testing.
        """
        self.huey.immediate = immediate
        self.huey.immediate_use_memory = immediate

    @staticmethod
    def _normalize_to_utc_str(ts: str) -> str:
        """
        Accepts ISO8601 or 'YYYY-MM-DD HH:MM:SS[.fff]' with optional 'Z' or offset.
        Returns UTC as 'YYYY-MM-DD HH:MM:SS.sss' (millisecond precision) to match
        SQLite's STRFTIME('%Y-%m-%d %H:%M:%f','now') format used in last_update.
        """
        if not ts:
            return "1970-01-01 00:00:00.000"

        s = ts.strip()

        if s.endswith("Z"):
            s = s[:-1] + "+00:00"

        dt = None
        try:
            dt = datetime.fromisoformat(s)
        except ValueError:
            try:
                if " " in s and "T" not in s:
                    dt = datetime.fromisoformat(s.replace(" ", "T"))
            except ValueError:
                dt = None

        if dt is None:
            for fmt in ("%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S"):
                try:
                    dt = datetime.strptime(s, fmt)
                    break
                except ValueError:
                    continue

        if dt is None:
            return "1970-01-01 00:00:00.000"

        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        else:
            dt = dt.astimezone(timezone.utc)

        ms = dt.microsecond // 1000
        return dt.strftime(f"%Y-%m-%d %H:%M:%S.{ms:03d}")

    def _register_signals(self):
        """Attach Huey lifecycle signal handlers to keep 'task_copy' in sync:
        - SIGNAL_ENQUEUED: insert or replace a row with status `not_started`
        - SIGNAL_EXECUTING: update the row to status `started`
        - SIGNAL_COMPLETE: update the row to status `finished`
        - SIGNAL_ERROR: update the row to status `error` and store the exception
        All writes stamp last_update with microsecond precision to avoid same-second
        conflicts.
        """

        def exec_sql(sql, params=()):
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(sql, params)

        NOW_MICRO = "STRFTIME('%Y-%m-%d %H:%M:%f','now')"

        @self.huey.signal(SIGNAL_ENQUEUED)
        def on_enqueue(signal, task):
            job_type = task.args[0].__class__.__name__
            job_name = None

            try:
                if hasattr(task.args[0], "get_job_name"):
                    job_name = task.args[0].get_job_name()
            except Exception:
                pass

            exec_sql(
                (
                    "INSERT OR REPLACE INTO task_copy "
                    "(id, task_type, job_name, status, last_update) "
                    f"VALUES (?, ?, ?, ?, {NOW_MICRO})"
                ),
                (task.id, job_type, job_name, "not_started"),
            )

        @self.huey.signal(SIGNAL_EXECUTING)
        def on_start(signal, task):
            exec_sql(
                (
                    "UPDATE task_copy SET status = ?, "
                    f"last_update = {NOW_MICRO} "
                    "WHERE id = ?"
                ),
                ("started", task.id),
            )

        @self.huey.signal(SIGNAL_COMPLETE)
        def on_success(signal, task, *args):
            # Guard: don't overwrite a cancel that raced with completion
            exec_sql(
                (
                    "UPDATE task_copy SET status = ?, progress = 100, "
                    f"last_update = {NOW_MICRO} "
                    "WHERE id = ? AND status NOT IN ('cancelled', 'killed')"
                ),
                ("finished", task.id),
            )

        @self.huey.signal(SIGNAL_ERROR)
        def on_error(signal, task, exc):
            # Do not overwrite terminal states set by the cancel/watchdog path
            exec_sql(
                (
                    "UPDATE task_copy SET status = ?, "
                    f"last_update = {NOW_MICRO}, "
                    "error_msg = ? "
                    "WHERE id = ? AND status NOT IN ('cancelled', 'killed')"
                ),
                ("error", str(exc), task.id),
            )

    def _enable_wal(self):
        """
        Enable Write-Ahead Logging mode in SQLite to improve concurrent reads/writes.
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("PRAGMA journal_mode=WAL;")
            conn.execute("PRAGMA synchronous=NORMAL;")

    def _ensure_task_copy_table(self):
        """Ensure the 'task_copy' table exists with all required columns.

        Columns:
        - id (TEXT PRIMARY KEY): unique identifier for the job (UUID as text)
        - task_type (TEXT NOT NULL): the name of the Huey task
        - job_name (TEXT): a more descriptive name for the job (from get_job_name)
        - enqueued_at (DATETIME NOT NULL): defaults to CURRENT_TIMESTAMP (UTC)
        - status (TEXT NOT NULL): one of: 'not_started', 'started', 'finished',
          'deleted', 'error', 'cancelled', 'killed'
        - last_update (DATETIME NOT NULL): defaults to CURRENT_TIMESTAMP (UTC)
        - error_msg (TEXT): optional error message when a task fails
        - pid (INTEGER): OS PID of the worker subprocess while running; NULL otherwise
        - progress (REAL): optional completion percentage in the range 0-100
        - progress_message (TEXT): optional short description of the current phase
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS task_copy (
                    id TEXT PRIMARY KEY,
                    task_type TEXT NOT NULL,
                    job_name TEXT,
                    enqueued_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    status TEXT NOT NULL,
                    last_update DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    error_msg TEXT,
                    pid INTEGER,
                    progress REAL,
                    progress_message TEXT
                )
                """)
            # Idempotent migration: add pid column to pre-existing databases
            existing = {
                row[1]
                for row in conn.execute("PRAGMA table_info(task_copy)").fetchall()
            }
            if "pid" not in existing:
                conn.execute("ALTER TABLE task_copy ADD COLUMN pid INTEGER")
            conn.execute(
                (
                    "CREATE INDEX IF NOT EXISTS idx_task_copy_last_update "
                    "ON task_copy(last_update, id)"
                )
            )

    def _ensure_progress_columns(self):
        """Add the progress columns to an existing 'task_copy' table.

        Installs created before progress tracking existed have a 'task_copy'
        table without the 'progress' and 'progress_message' columns. SQLite has
        no 'ADD COLUMN IF NOT EXISTS', so inspect the current columns via
        PRAGMA table_info and add only the ones that are missing.
        """
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.execute("PRAGMA table_info(task_copy)")
            existing = {row[1] for row in cur.fetchall()}
            if "progress" not in existing:
                conn.execute("ALTER TABLE task_copy ADD COLUMN progress REAL")
            if "progress_message" not in existing:
                conn.execute("ALTER TABLE task_copy ADD COLUMN progress_message TEXT")

    def status(self, job_id: str) -> dict:
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute(
            """
            SELECT status, last_update, error_msg, job_name, progress,
                   progress_message
            FROM task_copy WHERE id = ?
            """,
            (str(job_id),),
        )
        row = cur.fetchone()
        conn.close()
        if not row:
            raise JobQueueError(f"No job with id={job_id}")
        return {
            "status": row[0],
            "updated": row[1],
            "error": row[2],
            "job_name": row[3],
            "progress": row[4],
            "progress_message": row[5],
        }

    def report_progress(
        self, job_id: str, progress: float | None, message: str | None = None
    ) -> None:
        """Update the progress of a running job.

        Parameters
        ----------
        job_id : str
            The UUID of the job (its Huey task id).
        progress : float or None
            Completion percentage in the range 0-100, or None for jobs whose
            total work is unknown (the frontend renders an indeterminate bar).
        message : str or None
            Optional short description of the current phase.

        Notes
        -----
        This also refreshes 'last_update' so the change surfaces through
        'changes_since' and the frontend polling channel.
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                (
                    "UPDATE task_copy SET progress = ?, progress_message = ?, "
                    "last_update = STRFTIME('%Y-%m-%d %H:%M:%f','now') "
                    "WHERE id = ?"
                ),
                (progress, message, str(job_id)),
            )

    def put(self, job: BaseJob) -> int:
        result = self._execute(job)

        return result

    def to_list(self) -> list[dict]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute("""
                SELECT id, task_type, job_name, enqueued_at, status, last_update,
                       error_msg, progress, progress_message
                FROM task_copy
                ORDER BY last_update DESC
                """)
            return [dict(row) for row in cur.fetchall()]

    def changes_since(self, since: str) -> list[dict]:
        """
        Return jobs whose last_update is strictly greater than the given timestamp.
        The 'since' timestamp is normalized to UTC with microseconds to avoid
        same-second race conditions.
        """
        cutoff = self._normalize_to_utc_str(since)
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute(
                """
                SELECT id, task_type, job_name, enqueued_at, status, last_update,
                        error_msg, progress, progress_message
                FROM task_copy
                WHERE last_update >= ?
                ORDER BY last_update DESC
                """,
                (cutoff,),
            )
            return [dict(row) for row in cur.fetchall()]

    def peek(self, job_id: str | None = None) -> BaseJob:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            if job_id is not None:
                cur.execute(
                    "SELECT data FROM task WHERE id = ? AND queue = ? LIMIT 1",
                    (job_id, self.huey.storage.name),
                )
            else:
                cur.execute(
                    (
                        "SELECT data FROM task WHERE queue = ? "
                        "ORDER BY priority DESC, id ASC LIMIT 1"
                    ),
                    (self.huey.storage.name,),
                )
            row = cur.fetchone()
        if not row:
            raise JobQueueError("Queue is empty")
        payload = self.serializer.loads(row[0])
        return payload[6][0]

    def get(self, job_id: str | None = None) -> BaseJob:
        """
        Get a job from the queue and remove it.
        If job_id is provided, get and remove that specific job.
        Otherwise, get the highest priority job.
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.isolation_level = None
            cur = conn.cursor()
            cur.execute("BEGIN IMMEDIATE")
            if job_id is not None:
                cur.execute(
                    "SELECT id, data FROM task WHERE id = ? AND queue = ? LIMIT 1",
                    (job_id, self.huey.storage.name),
                )
            else:
                cur.execute(
                    (
                        "SELECT id, data FROM task WHERE queue = ? "
                        "ORDER BY priority DESC, id ASC LIMIT 1"
                    ),
                    (self.huey.storage.name,),
                )
            row = cur.fetchone()
            if not row:
                conn.execute("ROLLBACK")
                raise JobQueueError("Queue is empty")
            jid, blob = row
            cur.execute("DELETE FROM task WHERE id = ?", (jid,))
            conn.execute("COMMIT")
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                (
                    "UPDATE task_copy SET status = ?, "
                    "last_update = STRFTIME('%Y-%m-%d %H:%M:%f','now') "
                    "WHERE id = ?"
                ),
                ("deleted", jid),
            )
        return self.serializer.loads(blob)[6][0]

    def is_empty(self) -> bool:
        """
        Check if the queue is empty.
        Returns False if either:
        1. There are pending tasks in the 'task' table, OR
        2. There are tasks with 'started' status in the 'task_copy' table
        """
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()

            cur.execute(
                "SELECT 1 FROM task WHERE queue = ? LIMIT 1",
                (self.huey.storage.name,),
            )
            task_empty = cur.fetchone() is None

            if not task_empty:
                return False

            cur.execute("SELECT 1 FROM task_copy WHERE status = 'started' LIMIT 1")
            no_started_tasks = cur.fetchone() is None

            return task_empty and no_started_tasks

    async def async_get(self) -> BaseJob:
        while True:
            try:
                return self.get()
            except JobQueueError:
                await asyncio.sleep(0.1)

    def cancel(self, job_id: str, *, reason: str = "cancelled") -> bool:
        """Cancel the job with *job_id*, regardless of whether it has started.

        - Not-started jobs: removed from the Huey task table and marked cancelled
          in task_copy (entity marked as error via the job's own method).
        - Running jobs: task_copy status is set to *reason* first (so that
          SIGNAL_ERROR cannot overwrite it), then the worker subprocess is killed.

        Returns True if a job was found and acted on, False otherwise.
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cur = conn.cursor()
                cur.execute("SELECT status, pid FROM task_copy WHERE id = ?", (job_id,))
                row = cur.fetchone()

            if not row:
                return False

            current_status = row["status"]
            pid = row["pid"]

            # ── Already fully gone — nothing to do ───────────────────────────
            if current_status == "deleted":
                return False

            # ── Terminal state: dismiss (remove from UI list) ─────────────────
            # finished / error / cancelled / killed → user clicks X to dismiss
            if current_status in ("finished", "error", "cancelled", "killed"):
                return self._dismiss(job_id)

            # ── Not started yet (still in the Huey task table) ───────────────
            if current_status == "not_started":
                return self._cancel_queued(job_id)

            # ── Running (started) ─────────────────────────────────────────────
            if current_status == "started":
                return self._cancel_running(job_id, pid, reason)

            return False

        except Exception as e:
            log.exception(f"Error cancelling job {job_id}: {e}")
            return False

    def _cancel_queued(self, job_id: str) -> bool:
        """Remove a not-yet-started job from the Huey task table."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cur = conn.cursor()
                cur.execute(
                    "SELECT id, data FROM task WHERE queue = ?",
                    (self.huey.storage.name,),
                )
                numeric_id = None
                job_obj = None
                for row in cur.fetchall():
                    try:
                        task_data = self.serializer._deserialize(row["data"])
                        if task_data[0] == job_id:
                            numeric_id = row["id"]
                            job_obj = task_data[6][0]
                            break
                    except Exception:
                        continue

                if numeric_id is not None:
                    cur.execute("DELETE FROM task WHERE id = ?", (numeric_id,))
                    with suppress(Exception):
                        job_obj.set_status_as_error()

                NOW_MICRO = "STRFTIME('%Y-%m-%d %H:%M:%f','now')"
                _terminal = "('cancelled','killed','finished','error')"
                cur.execute(
                    f"UPDATE task_copy SET status='cancelled', last_update={NOW_MICRO}"
                    f" WHERE id = ? AND status NOT IN {_terminal}",
                    (job_id,),
                )
                return numeric_id is not None or cur.rowcount > 0
        except Exception as e:
            log.exception(f"Error cancelling queued job {job_id}: {e}")
            return False

    def _cancel_running(self, job_id: str, pid, reason: str) -> bool:
        """Kill the worker subprocess for a running job."""
        NOW_MICRO = "STRFTIME('%Y-%m-%d %H:%M:%f','now')"
        # Mark status BEFORE killing so SIGNAL_ERROR guard preserves it.
        # Only kill if the UPDATE matched — if the job already finished, the
        # stale PID belongs to the next job's worker.
        marked = False
        _terminal = "('cancelled','killed','finished','error')"
        try:
            with sqlite3.connect(self.db_path) as conn:
                cur = conn.execute(
                    f"UPDATE task_copy SET status=?, last_update={NOW_MICRO}"
                    f" WHERE id=? AND status NOT IN {_terminal}",
                    (reason, job_id),
                )
                marked = cur.rowcount > 0
        except Exception as e:
            log.exception(f"Failed to mark task_copy for {job_id}: {e}")
            return False

        if marked and pid is not None:
            try:
                _terminate_pid(int(pid), grace_seconds=30)
            except Exception as e:
                log.warning(f"Could not terminate PID {pid} for job {job_id}: {e}")

        return marked

    def _dismiss(self, job_id: str) -> bool:
        """Remove a terminal job from task_copy so it disappears from the UI."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cur = conn.cursor()
                cur.execute("DELETE FROM task_copy WHERE id = ?", (job_id,))
                return cur.rowcount > 0
        except Exception as e:
            log.exception(f"Error dismissing job {job_id}: {e}")
            return False

    def delete_from_db(self, job_id: str) -> bool:
        """
        Delete a job from both task and task_copy tables.

        Args:
            job_id: The UUID of the job to delete

        Returns:
            bool: True if the job was deleted from at least one table
        """
        deleted_from_any = False

        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cur = conn.cursor()

                cur.execute(
                    "SELECT id, data FROM task WHERE queue = ?",
                    (self.huey.storage.name,),
                )

                numeric_id = None
                row_data = None

                for row in cur.fetchall():
                    try:
                        task_data = self.serializer._deserialize(row["data"])
                        if task_data[0] == job_id:
                            numeric_id = row["id"]
                            row_data = task_data
                            break
                    except Exception:
                        continue

                if numeric_id is not None:
                    cur.execute("DELETE FROM task WHERE id = ?", (numeric_id,))
                    try:
                        row_data[6][0].set_status_as_error()
                    except Exception as e:
                        log.exception(f"Error setting job status to error: {e}")
                    deleted_from_any = True

                cur.execute("DELETE FROM task_copy WHERE id = ?", (job_id,))
                if cur.rowcount > 0:
                    deleted_from_any = True

            return deleted_from_any
        except Exception as e:
            log.exception(f"Error deleting job: {e}")
            return False

    def start_watchdog(self, interval: float = 10.0) -> None:
        """Start a daemon thread that detects crashed worker subprocesses.

        When a worker process dies unexpectedly (OOM, segfault) without going
        through the normal cancel path, its status stays 'started' forever.
        This watchdog polls for started jobs whose PID no longer exists and
        marks them as 'killed'.
        """

        def _watchdog():
            import psutil

            NOW_MICRO = "STRFTIME('%Y-%m-%d %H:%M:%f','now')"
            while True:
                try:
                    with sqlite3.connect(self.db_path) as conn:
                        conn.row_factory = sqlite3.Row
                        rows = conn.execute(
                            "SELECT id, pid FROM task_copy"
                            " WHERE status='started' AND pid IS NOT NULL"
                        ).fetchall()

                    for row in rows:
                        huey_id = row["id"]
                        pid = row["pid"]
                        try:
                            alive = psutil.pid_exists(int(pid))
                        except Exception:
                            alive = True  # Assume alive if we can't check
                        if not alive:
                            try:
                                with sqlite3.connect(self.db_path) as conn:
                                    conn.execute(
                                        f"UPDATE task_copy SET status='killed', "
                                        f"pid=NULL, last_update={NOW_MICRO}, "
                                        "error_msg='Worker process died unexpectedly' "
                                        "WHERE id=? AND status='started'",
                                        (huey_id,),
                                    )
                                self._mark_entity_error(huey_id)
                                log.warning(
                                    f"Watchdog detected dead worker for job {huey_id} "
                                    f"(PID {pid}); marked as killed"
                                )
                            except Exception:
                                log.exception(
                                    f"Watchdog failed to mark job {huey_id} as killed"
                                )
                except Exception:
                    log.exception("Watchdog loop error")
                time.sleep(interval)

        t = threading.Thread(target=_watchdog, daemon=True, name="job-watchdog")
        t.start()
        log.info("Job watchdog started (interval=%.1fs)", interval)

    def delete_all_jobs(self) -> int:
        """
        Delete all jobs from both task and task_copy tables.

        Returns:
            int: Number of jobs deleted
        """
        deleted_count = 0

        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cur = conn.cursor()

                cur.execute(
                    "SELECT id, data FROM task WHERE queue = ?",
                    (self.huey.storage.name,),
                )

                jobs_to_delete = []

                for row in cur.fetchall():
                    try:
                        job_data = self.serializer._deserialize(row["data"])
                        with suppress(Exception):
                            job_data[6][0].set_status_as_error()
                        jobs_to_delete.append(row["id"])
                    except Exception:
                        jobs_to_delete.append(row["id"])

                if jobs_to_delete:
                    placeholders = ",".join(["?"] * len(jobs_to_delete))
                    cur.execute(
                        f"DELETE FROM task WHERE id IN ({placeholders})", jobs_to_delete
                    )
                    deleted_count = cur.rowcount

                cur.execute("DELETE FROM task_copy")
                deleted_count += cur.rowcount

            return deleted_count
        except Exception as e:
            log.exception(f"Error deleting all jobs: {e}")
            return 0


_lp_str = os.environ.get("DASHAI_LOCAL_PATH")
_lp = Path(os.path.expanduser(_lp_str)) if _lp_str else Path.home() / ".DashAI"
_lp.mkdir(parents=True, exist_ok=True)
_job_queue = HueyJobQueue("job_queue", path_db=str(_lp))
huey = _job_queue.huey


@huey.on_startup()
def create_container_huey():
    from DashAI.back.container import build_container
    from DashAI.back.dependencies.config_builder import build_config_dict

    local_path = _lp
    logging_level = os.environ.get("DASHAI_LOGGING_LEVEL", "INFO")

    config = build_config_dict(local_path=local_path, logging_level=logging_level)
    build_container(config)

    # Start the PID-liveness watchdog for detecting crashed worker subprocesses
    _job_queue.start_watchdog(interval=10.0)

    # Pre-warm the persistent worker so the first job does not pay the spawn cost
    try:
        _job_queue._ensure_worker()
    except Exception:
        log.exception("Failed to pre-warm worker process; will retry on first job")
