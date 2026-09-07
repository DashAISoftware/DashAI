"""Frozen-build smoke test for the persistent-worker mechanics of the job queue.

This stub mirrors the process model that dashAI uses in packaged builds, with
none of the heavy ML dependencies, so it can be frozen with PyInstaller in a
couple of minutes and exercised in CI:

- Entry-point structure of ``DashAI/__main__.py``: ``multiprocessing.freeze_support()``
  inside the ``__main__`` block, before any app code.
- A consumer thread (like the embedded Huey consumer in frozen mode) that spawns
  a persistent worker via the ``spawn`` context, mirroring
  ``huey_job_queue._worker_loop`` / ``_ensure_worker`` / ``_run_in_subprocess``:
  SimpleQueue in, Queue out, ready handshake, dill-serialised jobs.
- The cancel path of ``huey_job_queue._terminate_pid``: SIGTERM (TerminateProcess
  on Windows), kill detection via ``proc.is_alive()`` with a final drain, then
  transparent respawn.

Exit codes:
- 0: full scenario passed (prints FROZEN-SMOKE-OK).
- 1: worker never became ready or a step failed (prints FROZEN-SMOKE-BROKEN).
- 3: a multiprocessing child re-entered the app instead of being diverted by
  freeze_support (prints STUB-CHILD-REENTERED-APP). This is the exact failure
  mode of a frozen build without freeze_support().

Set ``STUB_SKIP_FREEZE_SUPPORT=1`` to simulate a build without the
freeze_support() call: the run must then fail (CI asserts non-zero exit).
"""

import multiprocessing
import os
import queue
import signal
import sys
import threading
import time
from contextlib import suppress

import dill

READY_TIMEOUT = 60.0
BROKEN_TIMEOUT = 15.0


def _worker_loop(in_q, out_q) -> None:
    """Persistent worker, mirroring huey_job_queue._worker_loop."""
    out_q.put(dill.dumps({"ready": True}))

    if sys.platform != "win32":

        def _sigterm_handler(signum, frame):
            sys.exit(0)

        signal.signal(signal.SIGTERM, _sigterm_handler)

    while True:
        try:
            job_bytes = in_q.get()
        except (EOFError, OSError):
            break
        if job_bytes is None:
            break
        try:
            job = dill.loads(job_bytes)
            out_q.put(dill.dumps({"ok": True, "result": job()}))
        except SystemExit:
            break
        except Exception as exc:
            out_q.put(dill.dumps({"ok": False, "exc": repr(exc)}))


def _terminate_pid(pid: int, grace_seconds: float = 10.0) -> None:
    """Kill a worker by PID, mirroring huey_job_queue._terminate_pid."""
    try:
        if sys.platform == "win32":
            os.kill(pid, signal.SIGTERM)  # TerminateProcess on Windows
            return
        try:
            os.kill(pid, signal.SIGTERM)
        except ProcessLookupError:
            return
        deadline = time.monotonic() + grace_seconds
        while time.monotonic() < deadline:
            try:
                os.kill(pid, 0)
            except ProcessLookupError:
                return
            time.sleep(0.2)
        with suppress(ProcessLookupError):
            os.kill(pid, signal.SIGKILL)
    except ProcessLookupError:
        pass


def _quick_job():
    return sum(range(1000))


def _long_job():
    time.sleep(120)
    return "should-never-finish"


class WorkerManager:
    """Minimal replica of HueyJobQueue's persistent-worker management."""

    def __init__(self):
        self.proc = None
        self.in_q = None
        self.out_q = None

    def ensure_worker(self, timeout: float) -> None:
        if self.proc is not None and self.proc.is_alive():
            return
        ctx = multiprocessing.get_context("spawn")
        self.in_q = ctx.SimpleQueue()
        self.out_q = ctx.Queue()
        self.proc = ctx.Process(
            target=_worker_loop, args=(self.in_q, self.out_q), daemon=True
        )
        self.proc.start()
        msg = dill.loads(self.out_q.get(timeout=timeout))
        if not msg.get("ready"):
            raise RuntimeError(f"worker failed to initialise: {msg}")

    def run_job(self, fn) -> dict:
        """Send a job and poll for its result, detecting external kills."""
        self.in_q.put(dill.dumps(fn))
        while True:
            try:
                return dill.loads(self.out_q.get(timeout=0.5))
            except queue.Empty:
                if not self.proc.is_alive():
                    # Final drain: the result may have raced with the kill
                    try:
                        return dill.loads(self.out_q.get(timeout=0.1))
                    except queue.Empty:
                        return {"killed": True}


def _scenario() -> None:
    mgr = WorkerManager()

    print("step 1: spawning persistent worker from frozen binary")
    mgr.ensure_worker(timeout=READY_TIMEOUT)
    print(f"  worker ready (PID {mgr.proc.pid})")

    print("step 2: running a dill-serialised job")
    outcome = mgr.run_job(_quick_job)
    assert outcome.get("ok"), outcome
    assert outcome.get("result") == 499500, outcome
    print(f"  job result OK: {outcome['result']}")

    print("step 3: killing the worker mid-job (cancel path)")
    pid = mgr.proc.pid
    result_holder = {}

    def _consumer():
        result_holder["outcome"] = mgr.run_job(_long_job)

    t = threading.Thread(target=_consumer, daemon=True)
    t.start()
    time.sleep(2.0)  # let the worker pick up the job
    _terminate_pid(pid)
    t.join(timeout=30.0)
    assert not t.is_alive(), "consumer thread did not detect the kill"
    assert result_holder["outcome"] == {"killed": True}, result_holder["outcome"]
    print(f"  kill detected (PID {pid})")

    print("step 4: respawning worker and running another job")
    mgr.ensure_worker(timeout=READY_TIMEOUT)
    assert mgr.proc.pid != pid, "worker was not respawned"
    outcome = mgr.run_job(_quick_job)
    assert outcome.get("ok"), outcome
    assert outcome.get("result") == 499500, outcome
    print(f"  respawned worker (PID {mgr.proc.pid}) ran job OK")


def main() -> None:
    # The real app runs the consumer in a daemon thread in frozen mode; spawn
    # from a non-main thread is part of what this test must cover.
    broken = os.environ.get("STUB_SKIP_FREEZE_SUPPORT") == "1"
    errors = []

    def _consumer_thread():
        try:
            if broken:
                # Give up quickly: the worker can never become ready because
                # its process re-entered the app and exited.
                mgr = WorkerManager()
                mgr.ensure_worker(timeout=BROKEN_TIMEOUT)
            else:
                _scenario()
        except Exception as exc:
            errors.append(exc)

    t = threading.Thread(target=_consumer_thread)
    t.start()
    t.join(timeout=300.0)

    if t.is_alive() or errors:
        print(f"FROZEN-SMOKE-BROKEN: {errors or 'timed out'}")
        sys.exit(1)
    print("FROZEN-SMOKE-OK")


if __name__ == "__main__":
    if os.environ.get("STUB_SKIP_FREEZE_SUPPORT") != "1":
        # Same call, same position as in DashAI/__main__.py and DashAI/webview.py
        multiprocessing.freeze_support()
    if "--multiprocessing-fork" in sys.argv or "-c" in sys.argv:
        # A multiprocessing child was NOT diverted by freeze_support and is
        # about to run the whole app again. Bail out instead of recursing —
        # this is what happens in a real frozen build without freeze_support.
        print("STUB-CHILD-REENTERED-APP")
        sys.exit(3)
    main()
