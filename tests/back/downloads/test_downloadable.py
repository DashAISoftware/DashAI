import pathlib
from unittest import mock

import pytest
from kink import di

from DashAI.back.dependencies.downloads import downloadable as dl

_SENTINEL = object()


@pytest.fixture
def components_root(tmp_path):
    # kink Container has no .get(), so monkeypatch.setitem is not usable.
    # Save and restore the "config" key manually.
    try:
        old = di["config"]
    except KeyError:
        old = _SENTINEL
    di["config"] = {"COMPONENT_PATH": str(tmp_path)}
    yield pathlib.Path(tmp_path)
    if old is _SENTINEL:
        del di["config"]
    else:
        di["config"] = old


class _Dummy(dl.HFDownloadableMixin):
    HF_REPOS = [("owner/model-a", "model")]


def _populate(root: pathlib.Path, cls, repo_leaf: str):
    d = root / cls.__name__ / repo_leaf
    d.mkdir(parents=True)
    (d / "config.json").write_text("{}")


def test_component_dir_under_root(components_root):
    assert _Dummy.component_dir() == components_root / "_Dummy"


def test_is_downloaded_false_when_absent(components_root):
    assert _Dummy.is_downloaded() is False


def test_is_downloaded_true_when_present(components_root):
    _populate(components_root, _Dummy, "model-a")
    assert _Dummy.is_downloaded() is True


def test_is_downloaded_false_when_no_repos(components_root):
    class Empty(dl.HFDownloadableMixin):
        HF_REPOS = []

    assert Empty.is_downloaded() is False


def test_download_fetches_into_component_dir(components_root):
    calls = []
    with mock.patch.object(dl, "snapshot_download") as snap:
        _Dummy.download(lambda frac, msg: calls.append((frac, msg)))
    snap.assert_called_once_with(
        repo_id="owner/model-a",
        repo_type="model",
        local_dir=str(components_root / "_Dummy" / "model-a"),
        ignore_patterns=list(_Dummy.HF_IGNORE_PATTERNS),
    )
    assert calls[0] == (None, "Downloading owner/model-a")


def test_delete_removes_component_dir(components_root):
    _populate(components_root, _Dummy, "model-a")
    _Dummy.delete()
    assert not (components_root / "_Dummy").exists()


# ---------------------------------------------------------------------------
# 3-tuple (allow_patterns) support
# ---------------------------------------------------------------------------


class _DummyPartial(dl.HFDownloadableMixin):
    HF_REPOS = [("owner/model-a", "model", ["*8_0.gguf"])]


def test_download_3tuple_passes_allow_patterns(components_root):
    with mock.patch.object(dl, "snapshot_download") as snap:
        _DummyPartial.download(lambda frac, msg: None)
    snap.assert_called_once_with(
        repo_id="owner/model-a",
        repo_type="model",
        local_dir=str(components_root / "_DummyPartial" / "model-a"),
        allow_patterns=["*8_0.gguf"],
        ignore_patterns=list(_DummyPartial.HF_IGNORE_PATTERNS),
    )


def test_download_2tuple_no_allow_patterns(components_root):
    with mock.patch.object(dl, "snapshot_download") as snap:
        _Dummy.download(lambda frac, msg: None)
    _call_kwargs = snap.call_args.kwargs
    assert "allow_patterns" not in _call_kwargs


def test_is_downloaded_3tuple_true_when_present(components_root):
    _populate(components_root, _DummyPartial, "model-a")
    assert _DummyPartial.is_downloaded() is True


def test_is_downloaded_3tuple_false_when_absent(components_root):
    assert _DummyPartial.is_downloaded() is False


def test_is_downloaded_3tuple_false_when_empty_dir(components_root):
    d = components_root / "_DummyPartial" / "model-a"
    d.mkdir(parents=True)
    assert _DummyPartial.is_downloaded() is False
