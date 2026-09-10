import pytest
from kink import di

from DashAI.back.job.component_download_job import ComponentDownloadJob


@pytest.fixture(autouse=False)
def fake_registry():
    """Inject a minimal component_registry into the kink container."""

    class FakeComponent:
        REQUIRES_DOWNLOAD = True

        calls = {"download": 0}

        @classmethod
        def download(cls, report=None):
            cls.calls["download"] += 1
            report(None, "Downloading")

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
