"""Job that downloads the release file of a dashAI update."""

import logging
from pathlib import Path

from DashAI.back.job.base_job import BaseJob, JobError

log = logging.getLogger(__name__)


class UpdateDownloadJob(BaseJob):
    """Download and verify the installer of a newer dashAI release.

    Parameters
    ----------
    kwargs : dict
        Must contain ``asset`` (an ``UpdateAsset`` as a dict) and
        ``directory`` (where release files are stored).
    """

    def set_status_as_delivered(self) -> None:
        """No dedicated DB entity; nothing to mark as delivered."""

    def set_status_as_error(self) -> None:
        """No dedicated DB entity; nothing to mark as error."""

    def on_cancel(self) -> None:
        """Remove the partial file of a cancelled or killed download."""
        from DashAI.back.updates.download import remove_partial_downloads

        try:
            remove_partial_downloads(Path(self.kwargs["directory"]))
        except Exception:
            log.exception("on_cancel cleanup failed for UpdateDownloadJob")

    def get_job_name(self) -> str:
        """Return a descriptive name for the job.

        Returns
        -------
        str
            A human-readable name including the file name.
        """
        return f"Download update: {self.kwargs['asset']['name']}"

    def run(self) -> None:
        """Download the release file, reporting progress.

        Raises
        ------
        JobError
            If the download fails or the file does not pass verification.
        """
        from DashAI.back.updates.checker import UpdateAsset
        from DashAI.back.updates.download import UpdateDownloadError, download_asset

        asset = UpdateAsset(**self.kwargs["asset"])
        self.report_progress(0.0, "Starting download")
        try:
            download_asset(asset, Path(self.kwargs["directory"]), self.report_progress)
        except UpdateDownloadError as error:
            raise JobError(str(error)) from error
        self.report_progress(1.0, "Download complete")
