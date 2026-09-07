"""Writable location where DashAI plugin distributions live.

Plugins are never installed into the interpreter's own environment. The
packaged distributions ship a read only environment (a PyInstaller bundle, or
the squashfs image inside an AppImage), and in a uv managed checkout any
``uv run`` re-syncs ``.venv`` against ``uv.lock`` and uninstalls everything
that is not locked, plugins included. Instead every plugin is installed into a
per user directory that is added to ``sys.path`` on startup.

The directory is scoped by interpreter version because plugins may ship
compiled extension modules, which are only importable by the CPython version
they were built for.
"""

import importlib
import logging
import os
import pathlib
import site
import sys
from typing import Optional

logger = logging.getLogger(__name__)

DEFAULT_LOCAL_PATH = "~/.DashAI"
PLUGINS_DIR_NAME = "plugins"


def get_plugins_directory(local_path: Optional[os.PathLike] = None) -> pathlib.Path:
    """Resolve the directory that holds the installed plugin distributions.

    Parameters
    ----------
    local_path : Optional[os.PathLike]
        Base dashAI data directory. Defaults to the ``DASHAI_LOCAL_PATH``
        environment variable, and to ``~/.DashAI`` when that is unset.

    Returns
    -------
    pathlib.Path
        Absolute path of the version scoped plugins directory. The directory is
        not created by this function.
    """
    if local_path is None:
        local_path = os.environ.get("DASHAI_LOCAL_PATH") or DEFAULT_LOCAL_PATH

    base = pathlib.Path(local_path).expanduser().absolute()
    interpreter = f"py{sys.version_info.major}.{sys.version_info.minor}"
    return base / PLUGINS_DIR_NAME / interpreter


def activate_plugins_directory(
    local_path: Optional[os.PathLike] = None,
) -> pathlib.Path:
    """Create the plugins directory and make it importable.

    The directory is appended to ``sys.path`` (so distributions shipped with
    dashAI always win over a plugin's copy of the same package) and exported
    through ``PYTHONPATH`` so that child processes, such as the Huey consumer,
    see the plugins too. Import caches are invalidated so that plugins
    installed while the app is running are discoverable without a restart.

    Parameters
    ----------
    local_path : Optional[os.PathLike]
        Base dashAI data directory, forwarded to
        :func:`get_plugins_directory`.

    Returns
    -------
    pathlib.Path
        Absolute path of the activated plugins directory.
    """
    directory = get_plugins_directory(local_path)
    try:
        directory.mkdir(parents=True, exist_ok=True)
    except OSError:
        logger.exception("Could not create the plugins directory %s", directory)
        return directory

    path = str(directory)
    if path not in sys.path:
        site.addsitedir(path)

    entries = [
        entry for entry in os.environ.get("PYTHONPATH", "").split(os.pathsep) if entry
    ]
    if path not in entries:
        os.environ["PYTHONPATH"] = os.pathsep.join([path, *entries])

    importlib.invalidate_caches()
    return directory
