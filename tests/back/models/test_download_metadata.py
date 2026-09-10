from DashAI.back.dependencies.downloads.downloadable import HFDownloadableMixin
from DashAI.back.models.base_model import BaseModel


class _PlainModel(BaseModel):
    def save(self, filename): ...
    @classmethod
    def load(cls, filename): ...
    def train(self, x, y, xv, yv): ...


class _DownloadableModel(HFDownloadableMixin, BaseModel):
    HF_REPOS = [("owner/model", "model")]
    DOWNLOAD_SIZE_BYTES = 1234

    def save(self, filename): ...
    @classmethod
    def load(cls, filename): ...
    def train(self, x, y, xv, yv): ...


def test_plain_model_not_downloadable():
    meta = _PlainModel.get_metadata()
    assert meta["requires_download"] is False
    assert meta["download_size_bytes"] is None


def test_downloadable_model_metadata():
    meta = _DownloadableModel.get_metadata()
    assert meta["requires_download"] is True
    assert meta["download_size_bytes"] == 1234
