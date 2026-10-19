"""Install a downloaded update and close dashAI so it can be replaced.

Each install channel is replaced differently:

- Windows: the Inno Setup installer runs silently over the current install.
- AppImage: the new file takes the place of the running one and is started.
- macOS: the disk image is opened in Finder for the user to drag the app.

In every case dashAI exits afterwards, because a running app keeps its files
in use (and its port taken) and would block or clash with the new version.
"""

import hashlib
import logging
import os
import shutil
import subprocess
import sys
import tempfile
import threading
from pathlib import Path

from DashAI.back.updates.checker import UpdateAsset
from DashAI.back.updates.installation import InstallChannel

logger = logging.getLogger(__name__)

# Time left for the HTTP response to reach the frontend before exiting.
_EXIT_DELAY_SECONDS = 1.5
# Time the old AppImage gets to release the port before the new one starts.
_APPIMAGE_RESTART_DELAY_SECONDS = 3

# Variables the AppImage runtime and its entry point set for the running
# instance. The new instance must set its own, so they are not inherited.
_APPIMAGE_ENV = (
    "APPDIR",
    "APPIMAGE",
    "ARGV0",
    "OWD",
    "PYTHONHOME",
    "PYTHONPATH",
    "DASHAI_IN_TERMINAL",
)


class UpdateInstallError(Exception):
    """Raised when a downloaded update cannot be installed."""


def verify_file(path: Path, asset: UpdateAsset) -> None:
    """Check a downloaded file against the size and SHA-256 of its release.

    The file was verified when it was downloaded, but it may have sat on disk
    for days since then, so it is checked again right before it runs.

    Raises
    ------
    UpdateInstallError
        If the file does not match.
    """
    if asset.size is not None and path.stat().st_size != asset.size:
        raise UpdateInstallError(f"{path.name} is incomplete.")
    if asset.sha256 is None:
        return
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    if digest.hexdigest() != asset.sha256.lower():
        raise UpdateInstallError(f"{path.name} does not match its published SHA-256.")


def _launch_windows_installer(installer: Path) -> None:
    """Start the Inno Setup installer silently.

    ``os.startfile`` goes through ShellExecute, which shows the UAC prompt the
    installer needs to write to Program Files. ``/CLOSEAPPLICATIONS`` closes
    anything still holding the install files, and ``/RELAUNCH=1`` (read by
    installer/installer.iss) starts dashAI again once the install finishes.
    """
    log_file = installer.with_suffix(".log")
    arguments = (
        "/SILENT /SUPPRESSMSGBOXES /NORESTART /CLOSEAPPLICATIONS /RELAUNCH=1 "
        f'/LOG="{log_file}"'
    )
    os.startfile(str(installer), "open", arguments)  # noqa: S606


def _replace_appimage(new_file: Path) -> Path:
    """Put the downloaded AppImage in place of the running one.

    The running instance keeps working after its file is replaced: Linux
    keeps the old file alive while it is open, and the AppImage runtime has
    it mounted.

    Returns
    -------
    Path
        Path of the replaced AppImage.

    Raises
    ------
    UpdateInstallError
        If the running AppImage is unknown or its folder is not writable.
    """
    current = os.environ.get("APPIMAGE")
    if not current:
        raise UpdateInstallError("The running AppImage file is unknown.")
    target = Path(current)
    try:
        # Copy next to the target first so the final rename stays on one
        # file system and is atomic.
        handle, temp_name = tempfile.mkstemp(
            prefix=f".{target.name}.", suffix=".new", dir=target.parent
        )
        os.close(handle)
        temp = Path(temp_name)
        shutil.copyfile(new_file, temp)
        temp.chmod(0o755)
        os.replace(temp, target)
    except OSError as error:
        raise UpdateInstallError(
            f"Could not replace {target}: {error}. Download the new version "
            "and replace the file manually."
        ) from error
    return target


def _restart_appimage(appimage: Path) -> None:
    """Start the new AppImage once this instance has exited."""
    env = {key: value for key, value in os.environ.items() if key not in _APPIMAGE_ENV}
    subprocess.Popen(  # noqa: S603
        [
            "/bin/sh",
            "-c",
            f'sleep {_APPIMAGE_RESTART_DELAY_SECONDS}; exec "$0"',
            str(appimage),
        ],
        env=env,
        start_new_session=True,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def _open_disk_image(image: Path) -> None:
    """Open the disk image in Finder."""
    subprocess.Popen(["open", str(image)])  # noqa: S603, S607


def _stop_job_worker() -> None:
    """Terminate the job worker process so it does not outlive the app.

    The worker is a separate process that would keep the install files in use
    on Windows. Only the consumer's queue owns it; in a process without an
    embedded consumer this does nothing.
    """
    try:
        from DashAI.back.dependencies.job_queues import huey_job_queue

        huey_job_queue._job_queue.stop_worker()
    except Exception:
        logger.exception("Could not stop the job worker before exiting")


def _exit_app() -> None:
    """Stop the job worker and end the dashAI process."""
    logger.info("Closing dashAI to install the update.")
    _stop_job_worker()
    sys.stdout.flush()
    sys.stderr.flush()
    os._exit(0)


def schedule_exit() -> None:
    """Exit dashAI shortly, once the current HTTP response has been sent."""
    timer = threading.Timer(_EXIT_DELAY_SECONDS, _exit_app)
    timer.daemon = True
    timer.start()


def install_update(path: Path, asset: UpdateAsset, channel: InstallChannel) -> None:
    """Install a downloaded update for an install channel.

    The caller still has to call ``schedule_exit`` so the new version can take
    over.

    Parameters
    ----------
    path : Path
        The downloaded release file.
    asset : UpdateAsset
        The release file description, used to verify ``path``.
    channel : InstallChannel
        How the running dashAI was installed.

    Raises
    ------
    UpdateInstallError
        If the file does not verify, the channel cannot be updated from a
        file or the update could not be put in place.
    """
    verify_file(path, asset)
    if channel == InstallChannel.WINDOWS:
        _launch_windows_installer(path)
    elif channel == InstallChannel.APPIMAGE:
        _restart_appimage(_replace_appimage(path))
    elif channel == InstallChannel.MACOS:
        _open_disk_image(path)
    else:
        raise UpdateInstallError(
            f"Installs of type '{channel.value}' are not updated from a file."
        )
