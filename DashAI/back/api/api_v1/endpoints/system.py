import logging
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from kink import di
from pydantic import BaseModel

from DashAI.back.updates.checker import (
    UpdateAsset,
    UpdateInfo,
    check_for_updates,
    find_update_asset,
)
from DashAI.back.updates.download import downloaded_file
from DashAI.back.updates.install import (
    UpdateInstallError,
    install_update,
    schedule_exit,
)
from DashAI.back.updates.installation import detect_install_channel

logger = logging.getLogger(__name__)

router = APIRouter()


class UpdateDownloadStatus(BaseModel):
    """Whether this install can download an update and if it already did."""

    available: bool
    name: Optional[str] = None
    size: Optional[int] = None
    downloaded: bool = False
    jobs_running: bool = False


class UpdateInstallRequest(BaseModel):
    """Options of an install request."""

    # Installing closes dashAI, which kills running jobs, so the user has to
    # confirm that explicitly.
    stop_running_jobs: bool = False


def _update_asset(config: Dict[str, Any]) -> Optional[UpdateAsset]:
    """Return the update file for this install, unless update checks are off."""
    if not config["UPDATE_CHECK_ENABLED"]:
        return None
    return find_update_asset(config["UPDATE_CHECK_REPOSITORY"])


@router.get("/update-check", response_model=UpdateInfo)
def get_update_check(
    config: Dict[str, Any] = Depends(lambda: di["config"]),
) -> UpdateInfo:
    """Tell whether a newer dashAI version has been released.

    The answer from GitHub is cached, so calling this on every page load is
    fine. Setting ``UPDATE_CHECK_ENABLED=false`` turns the check off, for
    example on a shared server where users cannot update the install.

    Returns
    -------
    UpdateInfo
        The current and latest versions, the release notes and the download
        link for the detected install channel.
    """
    return check_for_updates(
        enabled=config["UPDATE_CHECK_ENABLED"],
        repository=config["UPDATE_CHECK_REPOSITORY"],
    )


@router.get("/update/download", response_model=UpdateDownloadStatus)
def get_update_download(
    config: Dict[str, Any] = Depends(lambda: di["config"]),
    job_queue=Depends(lambda: di["job_queue"]),
) -> UpdateDownloadStatus:
    """Tell whether the update file can be downloaded and if it already was.

    Returns
    -------
    UpdateDownloadStatus
        ``available`` is False when there is no newer release or this install
        channel is not updated from a file (pip, source, Docker).
    """
    asset = _update_asset(config)
    if asset is None:
        return UpdateDownloadStatus(available=False)
    path = downloaded_file(Path(config["UPDATES_PATH"]), asset)
    return UpdateDownloadStatus(
        available=True,
        name=asset.name,
        size=asset.size,
        downloaded=path is not None,
        jobs_running=not job_queue.is_empty(),
    )


@router.post("/update/download", status_code=status.HTTP_201_CREATED)
def start_update_download(
    config: Dict[str, Any] = Depends(lambda: di["config"]),
    job_queue=Depends(lambda: di["job_queue"]),
) -> Dict[str, Any]:
    """Enqueue a job that downloads the update file for this install.

    Returns
    -------
    dict
        ``{"id": job_id}`` of the enqueued download job.

    Raises
    ------
    HTTPException
        409 if there is no update file for this install or it is already
        downloaded.
    """
    from DashAI.back.job.update_download_job import UpdateDownloadJob

    asset = _update_asset(config)
    if asset is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="There is no update file to download for this installation",
        )
    directory = Path(config["UPDATES_PATH"])
    if downloaded_file(directory, asset) is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"{asset.name} is already downloaded",
        )
    job = UpdateDownloadJob(asset=asset.model_dump(), directory=str(directory))
    job.set_status_as_delivered()
    job_id = job_queue.put(job).id
    return {"id": job_id}


@router.post("/update/install", status_code=status.HTTP_202_ACCEPTED)
def install_downloaded_update(
    request: UpdateInstallRequest,
    config: Dict[str, Any] = Depends(lambda: di["config"]),
    job_queue=Depends(lambda: di["job_queue"]),
) -> Dict[str, str]:
    """Install the downloaded update and close dashAI.

    dashAI exits right after answering, so the response is the last thing the
    frontend hears from this process.

    Returns
    -------
    dict
        ``{"channel": <install channel>}``, so the frontend knows what the
        user will see next (an installer, a restart or a Finder window).

    Raises
    ------
    HTTPException
        409 if there is no downloaded update, or jobs are running and
        ``stop_running_jobs`` was not set. 500 if the update could not be put
        in place.
    """
    asset = _update_asset(config)
    path = downloaded_file(Path(config["UPDATES_PATH"]), asset) if asset else None
    if asset is None or path is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="There is no downloaded update to install",
        )
    if not request.stop_running_jobs and not job_queue.is_empty():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Jobs are running; installing would stop them",
        )
    channel = detect_install_channel()
    try:
        install_update(path, asset, channel)
    except UpdateInstallError as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(error)
        ) from error
    schedule_exit()
    return {"channel": channel.value}
