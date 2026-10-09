"""Tests for BaseGenerativeModel.get_metadata download fields."""

from DashAI.back.dependencies.downloads.downloadable import HFDownloadableMixin
from DashAI.back.models.base_generative_model import BaseGenerativeModel


class _PlainGenerativeModel(BaseGenerativeModel):
    def __init__(self, **kwargs):
        pass

    def generate(self, input):
        return []


class _DownloadableGenerativeModel(HFDownloadableMixin, BaseGenerativeModel):
    HF_REPOS = [("owner/x", "model")]
    DOWNLOAD_SIZE_BYTES = 1234

    def __init__(self, **kwargs):
        pass

    def generate(self, input):
        return []


def test_plain_generative_model_not_downloadable():
    meta = _PlainGenerativeModel.get_metadata()
    assert meta["requires_download"] is False
    assert meta["download_size_bytes"] is None


def test_downloadable_generative_model_metadata():
    meta = _DownloadableGenerativeModel.get_metadata()
    assert meta["requires_download"] is True
    assert meta["download_size_bytes"] == 1234
