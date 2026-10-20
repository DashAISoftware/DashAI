"""Find out which dashAI version is running and how it was installed.

Each install channel updates differently (a new Windows installer, a new
AppImage, ``pip install -U``, a ``git pull``...), so the update check needs
both answers to decide what to offer the user.
"""

import os
import platform
import sys
import tomllib
from enum import Enum
from importlib import metadata
from pathlib import Path
from typing import Optional

import DashAI

DISTRIBUTION_NAME = "dashAI"

# Docker creates this file at the root of every container.
_DOCKERENV_PATH = Path("/.dockerenv")


class InstallChannel(str, Enum):
    """How the running dashAI was installed."""

    WINDOWS = "windows"
    MACOS = "macos"
    APPIMAGE = "appimage"
    DOCKER = "docker"
    PIP = "pip"
    SOURCE = "source"
    UNKNOWN = "unknown"


def _project_root() -> Path:
    """Return the directory that contains the ``DashAI`` package."""
    return Path(DashAI.__file__).resolve().parent.parent


def _pyproject_version(project_root: Path) -> Optional[str]:
    """Read the version from a dashAI ``pyproject.toml`` next to the package.

    Parameters
    ----------
    project_root : Path
        Directory that contains the ``DashAI`` package.

    Returns
    -------
    Optional[str]
        The version, or None when there is no dashAI ``pyproject.toml`` there
        (the normal case for a pip install, where the parent is site-packages).
    """
    pyproject = project_root / "pyproject.toml"
    try:
        with pyproject.open("rb") as file:
            project = tomllib.load(file).get("project", {})
    except (OSError, tomllib.TOMLDecodeError):
        return None
    if project.get("name", "").lower() != DISTRIBUTION_NAME.lower():
        return None
    return project.get("version")


def get_installed_version() -> Optional[str]:
    """Return the version of the running dashAI.

    A source checkout or a Docker image carries its ``pyproject.toml``, which
    is read first: package metadata there can come from a stale
    ``DashAI.egg-info`` left in the repository root.

    Returns
    -------
    Optional[str]
        The version string, or None when it cannot be determined.
    """
    version = _pyproject_version(_project_root())
    if version:
        return version
    try:
        return metadata.version(DISTRIBUTION_NAME)
    except metadata.PackageNotFoundError:
        return None


def detect_install_channel() -> InstallChannel:
    """Detect how the running dashAI was installed.

    Returns
    -------
    InstallChannel
        The detected channel. The order of the checks matters: an AppImage
        also looks like a pip install, and a Docker image like a source tree.
    """
    # Same signals the launcher uses in DashAI/__main__.py.
    if os.environ.get("APPIMAGE") or os.environ.get("APPDIR"):
        return InstallChannel.APPIMAGE

    if getattr(sys, "frozen", False):
        system = platform.system()
        if system == "Windows":
            return InstallChannel.WINDOWS
        if system == "Darwin":
            return InstallChannel.MACOS
        return InstallChannel.UNKNOWN

    if _DOCKERENV_PATH.exists():
        return InstallChannel.DOCKER

    if (_project_root() / ".git").exists():
        return InstallChannel.SOURCE

    return InstallChannel.PIP
