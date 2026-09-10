import sqlite3
import time  # noqa: F401

import pytest

from DashAI.back.dependencies.job_queues.base_job_queue import JobQueueError
from DashAI.back.dependencies.job_queues.huey_job_queue import HueyJobQueue
from DashAI.back.job.base_job import BaseJob


class DummyJob(BaseJob):
    def run(self) -> None:
        return None

    def set_status_as_delivered(self) -> None:
        return None

    def set_status_as_error(self) -> None:
        return None

    def get_job_name(self) -> str:
        return "Test Job"


def test_empty_queue(test_job_queue: HueyJobQueue):
    assert test_job_queue.is_empty()

    job = DummyJob()
    job_id = test_job_queue.put(job).id
    assert isinstance(job_id, str)

    assert test_job_queue.is_empty()


def test_queue_jobs_list(test_job_queue: HueyJobQueue):
    jobs_list = test_job_queue.to_list()
    assert isinstance(jobs_list, list)
    assert len(jobs_list) == 0

    job_1 = DummyJob()
    job_1_id = test_job_queue.put(job_1).id
    time.sleep(0.05)

    jobs_list = test_job_queue.to_list()
    assert len(jobs_list) == 1
    assert jobs_list[0]["id"] == job_1_id
    assert jobs_list[0]["status"] == "finished"

    job_2 = DummyJob()
    job_2_id = test_job_queue.put(job_2).id
    time.sleep(0.05)

    jobs_list = test_job_queue.to_list()
    assert len(jobs_list) == 2
    assert jobs_list[0]["id"] == job_2_id
    assert jobs_list[1]["id"] == job_1_id


def test_job_status(test_job_queue: HueyJobQueue):
    job = DummyJob()
    job_id = test_job_queue.put(job).id

    status = test_job_queue.status(job_id)
    assert status["status"] == "finished"
    assert status["job_name"] == "Test Job"
    assert status["error"] is None


def test_delete_job(test_job_queue: HueyJobQueue):
    job = DummyJob()
    job_id = test_job_queue.put(job).id

    status = test_job_queue.status(job_id)
    assert status["status"] == "finished"

    result = test_job_queue.delete_from_db(job_id)
    assert result is True

    with pytest.raises(JobQueueError):
        test_job_queue.status(job_id)


def test_delete_all_jobs(test_job_queue: HueyJobQueue):
    jobs = []
    for _ in range(5):
        job = DummyJob()
        job_id = test_job_queue.put(job).id
        jobs.append(job_id)

    jobs_list = test_job_queue.to_list()
    assert len(jobs_list) == 5

    deleted = test_job_queue.delete_all_jobs()
    assert deleted >= 5

    jobs_list = test_job_queue.to_list()
    assert len(jobs_list) == 0


def test_get_nonexistent_job_status(test_job_queue: HueyJobQueue):
    with pytest.raises(JobQueueError):
        test_job_queue.status("nonexistent-job-id")


def test_peek_and_get_nonexistent(test_job_queue: HueyJobQueue):
    job = DummyJob()
    job_id = test_job_queue.put(job).id

    with pytest.raises(JobQueueError):
        test_job_queue.peek(job_id)

    with pytest.raises(JobQueueError):
        test_job_queue.get(job_id)


def test_completion_sets_progress_to_100(test_job_queue: HueyJobQueue):
    job = DummyJob()
    job_id = test_job_queue.put(job).id

    status = test_job_queue.status(job_id)
    assert status["status"] == "finished"
    assert status["progress"] == 100


def test_report_progress_updates_status(test_job_queue: HueyJobQueue):
    job = DummyJob()
    job_id = test_job_queue.put(job).id

    test_job_queue.report_progress(job_id, 42.0, "Halfway there")

    status = test_job_queue.status(job_id)
    assert status["progress"] == 42.0
    assert status["progress_message"] == "Halfway there"


def test_report_progress_none_is_indeterminate(test_job_queue: HueyJobQueue):
    job = DummyJob()
    job_id = test_job_queue.put(job).id

    test_job_queue.report_progress(job_id, None, "Working")

    status = test_job_queue.status(job_id)
    assert status["progress"] is None
    assert status["progress_message"] == "Working"


def test_report_progress_surfaces_in_changes(test_job_queue: HueyJobQueue):
    job = DummyJob()
    job_id = test_job_queue.put(job).id

    test_job_queue.report_progress(job_id, 25.0, "Quarter")

    changes = test_job_queue.changes_since("1970-01-01 00:00:00.000000")
    changed = next(j for j in changes if j["id"] == job_id)
    assert changed["progress"] == 25.0
    assert changed["progress_message"] == "Quarter"


def test_ensure_progress_columns_migrates_old_table(tmp_path):
    # Simulate an install created before progress tracking: a 'task_copy'
    # table without the progress columns.
    db_path = tmp_path / "legacy.db"
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE task_copy (
                id TEXT PRIMARY KEY,
                task_type TEXT NOT NULL,
                job_name TEXT,
                enqueued_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                status TEXT NOT NULL,
                last_update DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                error_msg TEXT
            )
            """
        )

    # Constructing the queue against the same directory must add the columns.
    HueyJobQueue("legacy", path_db=str(tmp_path))

    with sqlite3.connect(db_path) as conn:
        cols = {row[1] for row in conn.execute("PRAGMA table_info(task_copy)")}
    assert "progress" in cols
    assert "progress_message" in cols


def test_base_job_report_progress_noop_without_huey_id():
    # A job with no huey_id (e.g. immediate mode) must not raise.
    job = DummyJob()
    assert job.kwargs.get("huey_id") is None
    job.report_progress(0.5, "Should be ignored")
