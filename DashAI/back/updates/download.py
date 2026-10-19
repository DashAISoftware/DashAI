"""Download a release file and check that it arrived intact.

Release files weigh up to a few GB, so they are streamed to a temporary
``.part`` file, hashed while they are written and only renamed to their final
name once the size and SHA-256 published by GitHub match. A file with its
final name is therefore always complete.
"""

import hashlib
import logging
import os
import tempfile
from pathlib import Path
from typing import Callable, Optional

import httpx

from DashAI.back.updates.checker import UpdateAsset

logger = logging.getLogger(__name__)

PART_SUFFIX = ".part"
_CHUNK_SIZE = 1024 * 1024
_REQUEST_TIMEOUT_SECONDS = 30

ProgressCallback = Callable[[Optional[float], Optional[str]], None]


class UpdateDownloadError(Exception):
    """Raised when a release file cannot be downloaded or fails verification."""


def downloaded_file(directory: Path, asset: UpdateAsset) -> Optional[Path]:
    """Return the already downloaded file for an asset, if there is one.

    Only the size is compared here: hashing a file of a few GB on every
    status request would be slow, and the hash was checked before the file
    got its final name.

    Parameters
    ----------
    directory : Path
        Directory where release files are stored.
    asset : UpdateAsset
        The release file to look for.

    Returns
    -------
    Optional[Path]
        The path of the complete file, or None when it is missing.
    """
    path = directory / asset.name
    if not path.is_file():
        return None
    if asset.size is not None and path.stat().st_size != asset.size:
        return None
    return path


def remove_partial_downloads(directory: Path) -> None:
    """Delete leftover ``.part`` files of interrupted downloads."""
    for part in directory.glob(f"*{PART_SUFFIX}"):
        try:
            part.unlink()
        except OSError:
            logger.warning("Could not remove partial update file %s", part)


def _remove_other_files(directory: Path, keep: str) -> None:
    """Delete the files of previous updates, which are no longer needed.

    ``.part`` files are left alone: they may belong to a download in progress.
    """
    for path in directory.iterdir():
        if path.is_file() and path.name != keep and path.suffix != PART_SUFFIX:
            try:
                path.unlink()
            except OSError:
                logger.warning("Could not remove old update file %s", path)


def download_asset(
    asset: UpdateAsset,
    directory: Path,
    report: Optional[ProgressCallback] = None,
) -> Path:
    """Download a release file into a directory and verify it.

    Parameters
    ----------
    asset : UpdateAsset
        The release file to download.
    directory : Path
        Directory where release files are stored. Files of other versions in
        it are deleted.
    report : Optional[ProgressCallback]
        Called with the completed fraction (or None when the size is unknown)
        and a short message.

    Returns
    -------
    Path
        Path of the verified file.

    Raises
    ------
    UpdateDownloadError
        If the download fails or the file does not match the published size
        or SHA-256.
    """
    directory.mkdir(parents=True, exist_ok=True)
    existing = downloaded_file(directory, asset)
    if existing is not None:
        return existing
    _remove_other_files(directory, keep=asset.name)

    # A unique temporary name keeps two concurrent downloads of the same file
    # from writing into each other.
    handle, part_name = tempfile.mkstemp(
        prefix=f"{asset.name}.", suffix=PART_SUFFIX, dir=directory
    )
    part = Path(part_name)
    digest = hashlib.sha256()
    written = 0
    last_percent = -1
    try:
        with (
            os.fdopen(handle, "wb") as file,
            httpx.stream(
                "GET",
                asset.url,
                follow_redirects=True,
                timeout=_REQUEST_TIMEOUT_SECONDS,
            ) as response,
        ):
            response.raise_for_status()
            total = asset.size or int(response.headers.get("Content-Length") or 0)
            for chunk in response.iter_bytes(_CHUNK_SIZE):
                file.write(chunk)
                digest.update(chunk)
                written += len(chunk)
                if report is None:
                    continue
                if not total:
                    report(None, "Downloading update")
                    continue
                percent = int(written * 100 / total)
                if percent != last_percent:
                    last_percent = percent
                    report(written / total, "Downloading update")

        if asset.size is not None and written != asset.size:
            raise UpdateDownloadError(
                f"Downloaded {written} bytes of {asset.name}, expected {asset.size}."
            )
        if asset.sha256 is not None and digest.hexdigest() != asset.sha256.lower():
            raise UpdateDownloadError(
                f"{asset.name} does not match its published SHA-256."
            )
        final = directory / asset.name
        os.replace(part, final)
        return final
    except httpx.HTTPError as error:
        raise UpdateDownloadError(
            f"Could not download {asset.name}: {error}"
        ) from error
    finally:
        if part.exists():
            part.unlink()
