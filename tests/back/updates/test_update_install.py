import hashlib
import sys

import pytest

from DashAI.back.updates import install
from DashAI.back.updates.checker import UpdateAsset
from DashAI.back.updates.installation import InstallChannel

NEW_CONTENT = b"new AppImage"


def _asset(content):
    return UpdateAsset(
        name="dashAI-0.11.0-x64-linux.AppImage",
        url="https://example.com/linux.AppImage",
        size=len(content),
        sha256=hashlib.sha256(content).hexdigest(),
    )


def test_appimage_is_replaced_and_restarted(tmp_path, monkeypatch):
    running = tmp_path / "dashAI.AppImage"
    running.write_bytes(b"old AppImage")
    downloaded = tmp_path / "download.AppImage"
    downloaded.write_bytes(NEW_CONTENT)
    monkeypatch.setenv("APPIMAGE", str(running))
    launched = []
    monkeypatch.setattr(
        install.subprocess, "Popen", lambda args, **kwargs: launched.append(kwargs)
    )

    install.install_update(downloaded, _asset(NEW_CONTENT), InstallChannel.APPIMAGE)

    assert running.read_bytes() == NEW_CONTENT
    # AppImages only exist on Linux; Windows has no executable permission bits.
    if sys.platform != "win32":
        assert running.stat().st_mode & 0o111
    # The new instance must not inherit the running instance's AppImage paths.
    assert "APPIMAGE" not in launched[0]["env"]


def test_tampered_file_is_not_installed(tmp_path, monkeypatch):
    downloaded = tmp_path / "download.AppImage"
    downloaded.write_bytes(b"something else")
    monkeypatch.setattr(
        install.subprocess, "Popen", lambda *args, **kwargs: pytest.fail("ran")
    )

    with pytest.raises(install.UpdateInstallError):
        install.install_update(
            downloaded, _asset(b"x" * len(b"something else")), InstallChannel.MACOS
        )
