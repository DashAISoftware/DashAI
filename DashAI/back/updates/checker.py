"""Check GitHub Releases for a newer dashAI version.

The release workflow publishes every version as a GitHub Release with one
installer per platform, so the latest release says both whether an update
exists and which file the user needs for their install channel.
"""

import logging
import platform
import re
import threading
import time
from typing import Optional

import httpx
from packaging.version import InvalidVersion, Version
from pydantic import BaseModel

from DashAI.back.updates.installation import (
    InstallChannel,
    detect_install_channel,
    get_installed_version,
)

logger = logging.getLogger(__name__)

DEFAULT_REPOSITORY = "DashAISoftware/DashAI"
_LATEST_RELEASE_URL = "https://api.github.com/repos/{repository}/releases/latest"
# GitHub "owner/name": letters, digits, "-", "_" and ".".
_REPOSITORY_PATTERN = re.compile(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+")
_REQUEST_TIMEOUT_SECONDS = 5

# Unauthenticated GitHub API calls are limited to 60 per hour per IP, and a
# whole classroom may share one IP, so a successful answer is reused for a
# day. A failed check (offline, rate limited) is retried after an hour instead
# of on every page load.
_SUCCESS_TTL_SECONDS = 24 * 60 * 60
_FAILURE_TTL_SECONDS = 60 * 60

_cache_lock = threading.Lock()
# (expires_at, repository, release). release is None when the fetch failed.
_cache: Optional[tuple[float, str, Optional[dict]]] = None


class UpdateInfo(BaseModel):
    """What the frontend needs to tell the user about updates."""

    enabled: bool
    channel: InstallChannel
    current_version: Optional[str]
    latest_version: Optional[str] = None
    update_available: bool = False
    release_notes: Optional[str] = None
    release_url: Optional[str] = None
    download_url: Optional[str] = None
    published_at: Optional[str] = None
    check_failed: bool = False


class UpdateAsset(BaseModel):
    """A release file that installs dashAI for one install channel."""

    name: str
    url: str
    size: Optional[int] = None
    sha256: Optional[str] = None


def _fetch_latest_release(repository: str) -> Optional[dict]:
    """Ask GitHub for the latest published release of a repository.

    Parameters
    ----------
    repository : str
        The GitHub repository as "owner/name".

    Returns
    -------
    Optional[dict]
        The release as returned by the GitHub API, or None when it could not
        be fetched. Drafts and pre-releases are never returned by this API.
    """
    if not _REPOSITORY_PATTERN.fullmatch(repository):
        logger.warning("Invalid update repository %r, expected owner/name", repository)
        return None
    try:
        response = httpx.get(
            _LATEST_RELEASE_URL.format(repository=repository),
            headers={
                "Accept": "application/vnd.github+json",
                "User-Agent": "dashAI-update-check",
            },
            timeout=_REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        return response.json()
    except (httpx.HTTPError, ValueError) as error:
        logger.info("Could not check for dashAI updates: %s", error)
        return None


def _get_latest_release(repository: str) -> Optional[dict]:
    """Return the latest release, fetching it only when the cache expired."""
    global _cache
    with _cache_lock:
        now = time.monotonic()
        if _cache is not None and _cache[0] > now and _cache[1] == repository:
            return _cache[2]
        release = _fetch_latest_release(repository)
        ttl = _SUCCESS_TTL_SECONDS if release is not None else _FAILURE_TTL_SECONDS
        _cache = (now + ttl, repository, release)
        return release


def _parse_version(text: Optional[str]) -> Optional[Version]:
    """Parse a version string, accepting a leading "v" as in release tags."""
    if not text:
        return None
    try:
        return Version(text.removeprefix("v"))
    except InvalidVersion:
        return None


def _asset_suffix(channel: InstallChannel) -> Optional[str]:
    """Return the end of the release file name for an install channel.

    Release files are named ``dashAI-<version>-<arch>-<os>.<ext>`` by the
    release workflow, for example ``dashAI-0.10.0-arm-osx.dmg``.
    """
    machine = platform.machine().lower()
    arch = "arm" if machine in ("arm64", "aarch64") else "x64"
    suffixes = {
        InstallChannel.WINDOWS: "-x64-windows.exe",
        InstallChannel.MACOS: f"-{arch}-osx.dmg",
        InstallChannel.APPIMAGE: f"-{arch}-linux.AppImage",
    }
    return suffixes.get(channel)


def _select_asset(release: dict, channel: InstallChannel) -> Optional[UpdateAsset]:
    """Return the release file for an install channel.

    Returns
    -------
    Optional[UpdateAsset]
        The file, or None when the channel has no installer (pip, source,
        Docker) or the release does not ship one for this platform.
    """
    suffix = _asset_suffix(channel)
    if suffix is None:
        return None
    for asset in release.get("assets", []):
        name = asset.get("name", "")
        if not name.endswith(suffix) or not asset.get("browser_download_url"):
            continue
        # GitHub publishes the digest as "sha256:<hex>".
        algorithm, _, value = (asset.get("digest") or "").partition(":")
        return UpdateAsset(
            name=name,
            url=asset["browser_download_url"],
            size=asset.get("size"),
            sha256=value if algorithm == "sha256" and value else None,
        )
    return None


def _is_newer(release: dict, current_version: Optional[str]) -> bool:
    """Tell whether a release is newer than the running version."""
    latest = _parse_version(release.get("tag_name"))
    current = _parse_version(current_version)
    return bool(latest and current and latest > current)


def find_update_asset(
    repository: str = DEFAULT_REPOSITORY,
) -> Optional[UpdateAsset]:
    """Return the file that updates this install, if a newer release has one.

    Parameters
    ----------
    repository : str
        The GitHub repository whose releases are checked, as "owner/name".

    Returns
    -------
    Optional[UpdateAsset]
        The release file for the detected install channel, or None when there
        is no newer release, GitHub is unreachable or the channel cannot be
        updated from a downloaded file.
    """
    release = _get_latest_release(repository)
    if release is None or not _is_newer(release, get_installed_version()):
        return None
    return _select_asset(release, detect_install_channel())


def check_for_updates(
    enabled: bool = True, repository: str = DEFAULT_REPOSITORY
) -> UpdateInfo:
    """Compare the running dashAI with the latest GitHub release.

    Never raises on network problems: an unreachable GitHub is reported with
    ``check_failed`` so the app keeps working offline.

    Parameters
    ----------
    enabled : bool
        When False, nothing is requested from GitHub.
    repository : str
        The GitHub repository whose releases are checked, as "owner/name".

    Returns
    -------
    UpdateInfo
        The current version, the latest one and, when newer, where to get it.
    """
    channel = detect_install_channel()
    current_version = get_installed_version()
    info = UpdateInfo(enabled=enabled, channel=channel, current_version=current_version)
    if not enabled:
        return info

    release = _get_latest_release(repository)
    if release is None:
        info.check_failed = True
        return info

    latest = _parse_version(release.get("tag_name"))
    info.latest_version = str(latest) if latest else None
    info.release_notes = release.get("body")
    info.release_url = release.get("html_url")
    info.published_at = release.get("published_at")
    info.update_available = _is_newer(release, current_version)
    if info.update_available:
        asset = _select_asset(release, channel)
        info.download_url = asset.url if asset else None
    return info
