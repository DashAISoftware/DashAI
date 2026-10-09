import pytest
from kink import di

from DashAI.back.job.component_download_job import ComponentDownloadJob


@pytest.fixture(autouse=False)
def fake_registry():
    """Inject a minimal component_registry into the kink container."""

    class FakeComponent:
        REQUIRES_DOWNLOAD = True

        calls = {"download": 0, "delete": 0}

        @classmethod
        def download(cls, report=None):
            cls.calls["download"] += 1
            report(None, "Downloading")

        @classmethod
        def delete(cls):
            cls.calls["delete"] += 1

    registry = {"FakeComponent": {"class": FakeComponent}}
    di["component_registry"] = registry
    yield FakeComponent
    del di["component_registry"]


def test_run_downloads_component(fake_registry):
    job = ComponentDownloadJob(component_name="FakeComponent")
    job.run()
    assert fake_registry.calls["download"] == 1


def test_get_job_name_uses_component_name():
    job = ComponentDownloadJob(component_name="FakeComponent")
    assert "FakeComponent" in job.get_job_name()


@pytest.fixture
def broken_registry():
    """Inject a component whose download fails halfway."""

    class BrokenComponent:
        REQUIRES_DOWNLOAD = True

        deleted = False

        @classmethod
        def download(cls, report=None):
            raise OSError("connection reset")

        @classmethod
        def delete(cls):
            cls.deleted = True

    di["component_registry"] = {"BrokenComponent": {"class": BrokenComponent}}
    yield BrokenComponent
    del di["component_registry"]


def test_failed_download_is_deleted(broken_registry):
    """A partial download looks downloaded, so a failed one must be removed."""
    job = ComponentDownloadJob(component_name="BrokenComponent")
    with pytest.raises(OSError, match="connection reset"):
        job.run()
    assert broken_registry.deleted


def test_cancel_deletes_a_download_that_started(fake_registry):
    """A job that reached the consumer may have written files, so they go."""
    job = ComponentDownloadJob(component_name="FakeComponent", huey_id="job-1")
    job.on_cancel()
    assert fake_registry.calls["delete"] == 1


def test_cancel_while_queued_keeps_the_component(fake_registry):
    """A job cancelled before reaching the consumer wrote nothing to remove."""
    job = ComponentDownloadJob(component_name="FakeComponent")
    job.on_cancel()
    assert fake_registry.calls["delete"] == 0
