import pytest

from DashAI.back.updates import checker
from DashAI.back.updates.installation import InstallChannel

RELEASE = {
    "tag_name": "v0.11.0",
    "body": "Release notes",
    "html_url": "https://github.com/DashAISoftware/DashAI/releases/tag/v0.11.0",
    "published_at": "2026-10-01T00:00:00Z",
    "assets": [
        {
            "name": "dashAI-0.11.0-x64-windows.exe",
            "browser_download_url": "https://example.com/windows.exe",
        },
        {
            "name": "dashAI-0.11.0-arm-osx.dmg",
            "browser_download_url": "https://example.com/mac.dmg",
        },
    ],
}


@pytest.fixture
def install(monkeypatch):
    """Fake the running install and start every test with an empty cache."""
    monkeypatch.setattr(checker, "_cache", None)
    monkeypatch.setattr(checker, "get_installed_version", lambda: "0.10.0")
    monkeypatch.setattr(
        checker, "detect_install_channel", lambda: InstallChannel.WINDOWS
    )


def _fake_fetch(monkeypatch, release):
    calls = []

    def fetch(repository):
        calls.append(repository)
        return release

    monkeypatch.setattr(checker, "_fetch_latest_release", fetch)
    return calls


def test_newer_release_offers_the_installer_for_the_channel(install, monkeypatch):
    _fake_fetch(monkeypatch, RELEASE)

    info = checker.check_for_updates()

    assert info.update_available
    assert info.latest_version == "0.11.0"
    assert info.download_url == "https://example.com/windows.exe"


def test_offline_reports_failure_without_raising(install, monkeypatch):
    _fake_fetch(monkeypatch, None)

    info = checker.check_for_updates()

    assert info.check_failed
    assert not info.update_available
    assert info.current_version == "0.10.0"


def test_disabled_check_never_contacts_github(install, monkeypatch):
    calls = _fake_fetch(monkeypatch, RELEASE)

    info = checker.check_for_updates(enabled=False)

    assert not info.enabled
    assert not info.update_available
    assert calls == []


def test_release_is_cached_between_checks(install, monkeypatch):
    calls = _fake_fetch(monkeypatch, RELEASE)

    checker.check_for_updates()
    checker.check_for_updates()

    assert len(calls) == 1


def test_another_repository_is_not_served_from_the_cache(install, monkeypatch):
    calls = _fake_fetch(monkeypatch, RELEASE)

    checker.check_for_updates()
    checker.check_for_updates(repository="me/DashAI")

    assert calls == [checker.DEFAULT_REPOSITORY, "me/DashAI"]
