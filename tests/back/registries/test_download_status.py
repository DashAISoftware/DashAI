from DashAI.back.config_object import ConfigObject
from DashAI.back.dependencies.downloads.downloadable import DownloadableMixin
from DashAI.back.dependencies.registry import ComponentRegistry


class _FakeBase(ConfigObject):
    TYPE = "Model"


_STATE = {"downloaded": False}


class _FakeDownloadable(DownloadableMixin, _FakeBase):
    DOWNLOAD_SIZE_BYTES = 10

    @classmethod
    def is_downloaded(cls):
        return _STATE["downloaded"]

    @classmethod
    def download(cls, report=None): ...
    @classmethod
    def delete(cls): ...


def test_seed_sets_downloaded_flag():
    _STATE["downloaded"] = False
    registry = ComponentRegistry(initial_components=[_FakeDownloadable])
    assert registry["_FakeDownloadable"]["downloaded"] is False


def test_refresh_reconciles_single_component():
    _STATE["downloaded"] = False
    registry = ComponentRegistry(initial_components=[_FakeDownloadable])
    _STATE["downloaded"] = True
    assert registry.refresh_download_status("_FakeDownloadable") is True
    assert registry["_FakeDownloadable"]["downloaded"] is True
