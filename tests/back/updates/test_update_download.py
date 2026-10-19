import hashlib
from contextlib import contextmanager

import pytest

from DashAI.back.updates import download
from DashAI.back.updates.checker import UpdateAsset

CONTENT = b"new dashAI installer" * 1000


class _FakeResponse:
    headers = {"Content-Length": str(len(CONTENT))}

    def raise_for_status(self):
        pass

    def iter_bytes(self, chunk_size):
        for start in range(0, len(CONTENT), chunk_size):
            yield CONTENT[start : start + chunk_size]


@pytest.fixture
def fake_github(monkeypatch):
    """Serve CONTENT for any download and count the requests."""
    calls = []

    @contextmanager
    def stream(*args, **kwargs):
        calls.append(1)
        yield _FakeResponse()

    monkeypatch.setattr(download.httpx, "stream", stream)
    return calls


def _asset(sha256):
    return UpdateAsset(
        name="dashAI-0.11.0-arm-osx.dmg",
        url="https://example.com/mac.dmg",
        size=len(CONTENT),
        sha256=sha256,
    )


def test_verified_download_gets_its_final_name(tmp_path, fake_github):
    (tmp_path / "dashAI-0.10.0-arm-osx.dmg").write_bytes(b"old version")
    asset = _asset(hashlib.sha256(CONTENT).hexdigest())

    path = download.download_asset(asset, tmp_path)

    assert path.read_bytes() == CONTENT
    assert [p.name for p in tmp_path.iterdir()] == [asset.name]


def test_wrong_hash_leaves_no_file_behind(tmp_path, fake_github):
    with pytest.raises(download.UpdateDownloadError):
        download.download_asset(_asset("0" * 64), tmp_path)

    assert list(tmp_path.iterdir()) == []


def test_already_downloaded_file_is_not_fetched_again(tmp_path, fake_github):
    asset = _asset(hashlib.sha256(CONTENT).hexdigest())
    (tmp_path / asset.name).write_bytes(CONTENT)

    download.download_asset(asset, tmp_path)

    assert fake_github == []
