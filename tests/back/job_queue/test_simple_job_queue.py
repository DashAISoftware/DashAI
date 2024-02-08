import pytest

from DashAI.back.dependencies.job_queues import BaseJobQueue, SimpleJobQueue
from DashAI.back.dependencies.job_queues.base_job_queue import JobQueueError
from DashAI.back.job.base_job import BaseJob


class DummyJob(BaseJob):
    def run(self) -> None:
        return None

    def set_status_as_delivered(self) -> None:
        return None


@pytest.fixture(name="job_queue")
def fixture_job_queue() -> BaseJobQueue:
    queue = SimpleJobQueue()
    yield queue
    while not queue.is_empty():
        queue.get()


def test_empty_queue(job_queue: BaseJobQueue):
    assert job_queue.is_empty()

    job = DummyJob()
    job_queue.put(job)

    assert not job_queue.is_empty()


def test_queue_to_list(job_queue: BaseJobQueue):
    jobs = job_queue.to_list()
    assert isinstance(jobs, list)
    assert jobs == []

    job_1 = DummyJob()
    job_1_id = job_queue.put(job_1)
    jobs = job_queue.to_list()
    assert len(jobs) == 1
    assert jobs[0].id == job_1_id

    job_2 = DummyJob()
    job_2_id = job_queue.put(job_2)
    jobs = job_queue.to_list()
    assert jobs[0].id == job_1_id
    assert jobs[1].id == job_2_id


def test_enqueue_jobs(job_queue: BaseJobQueue):
    job_1 = DummyJob()
    job_1_id = job_queue.put(job_1)
    assert job_1.id == job_1_id

    job_2 = DummyJob()
    job_2_id = job_queue.put(job_2)
    assert job_2.id == job_2_id
    assert job_1_id != job_2_id

    job_3 = DummyJob()
    job_3_id = job_queue.put(job_3)
    assert job_3.id == job_3_id
    assert job_1_id != job_3_id
    assert job_2_id != job_3_id


def test_get_jobs(job_queue: BaseJobQueue):
    job_1 = DummyJob()
    job_1_id = job_queue.put(job_1)
    job_2 = DummyJob()
    job_2_id = job_queue.put(job_2)
    job_3 = DummyJob()
    job_3_id = job_queue.put(job_3)

    assert job_queue.get().id == job_1_id
    assert job_queue.get(job_3_id).id == job_3_id

    jobs = job_queue.to_list()
    assert len(jobs) == 1
    assert jobs[0].id == job_2_id


@pytest.mark.asyncio()
async def test_async_get_job(job_queue: BaseJobQueue):
    job_1 = DummyJob()
    job_1_id = job_queue.put(job_1)

    job = await job_queue.async_get()
    assert job.id == job_1_id


def test_peek_jobs(job_queue: BaseJobQueue):
    job_1 = DummyJob()
    job_1_id = job_queue.put(job_1)
    job_2 = DummyJob()
    job_2_id = job_queue.put(job_2)
    job_3 = DummyJob()
    job_3_id = job_queue.put(job_3)

    assert job_queue.peek().id == job_1_id
    assert job_queue.peek(job_3_id).id == job_3_id

    jobs = job_queue.to_list()
    assert len(jobs) == 3
    assert jobs[0].id == job_1_id
    assert jobs[1].id == job_2_id
    assert jobs[2].id == job_3_id


def test_get_from_empty_queue(job_queue: BaseJobQueue):
    with pytest.raises(JobQueueError):
        job_queue.get()
    with pytest.raises(JobQueueError):
        job_queue.get(job_id=0)


def test_peek_from_empty_queue(job_queue: BaseJobQueue):
    with pytest.raises(JobQueueError):
        job_queue.peek()
    with pytest.raises(JobQueueError):
        job_queue.peek(job_id=0)


def test_get_nonexistent_job(job_queue: BaseJobQueue):
    job = DummyJob()
    job_queue.put(job)
    with pytest.raises(JobQueueError):
        job_queue.get(job_id=-1)


def test_peek_nonexistent_job(job_queue: BaseJobQueue):
    job = DummyJob()
    job_queue.put(job)
    with pytest.raises(JobQueueError):
        job_queue.peek(job_id=-1)
