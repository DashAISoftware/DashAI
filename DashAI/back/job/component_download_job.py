"""Job that downloads a component's external artifacts."""

import logging

from kink import di

from DashAI.back.job.base_job import BaseJob, JobError

log = logging.getLogger(__name__)


class ComponentDownloadJob(BaseJob):
    """Download the artifacts required by a downloadable component.

    Parameters
    ----------
    kwargs : dict
        Must contain ``component_name`` (the component class name).
    """

    def set_status_as_delivered(self) -> None:
        """No dedicated DB entity; nothing to mark as delivered."""

    def set_status_as_error(self) -> None:
        """No dedicated DB entity; nothing to mark as error."""

    def get_job_name(self) -> str:
        """Return a descriptive name for the job.

        Returns
        -------
        str
            A human-readable name including the component name.
        """
        return f"Download: {self.kwargs.get('component_name', 'component')}"

    def run(self) -> None:
        """Resolve the component and download its artifacts, reporting progress.

        Raises
        ------
        JobError
            If the component is not registered or does not require a download.
        """
        component_registry = di["component_registry"]
        name = self.kwargs["component_name"]

        try:
            component_class = component_registry[name]["class"]
        except KeyError as e:
            raise JobError(f"Component {name} is not registered") from e

        if not getattr(component_class, "REQUIRES_DOWNLOAD", False):
            raise JobError(f"Component {name} does not require a download")

        self.report_progress(0.0, "Starting download")
        component_class.download(self.report_progress)
        self.report_progress(1.0, "Download complete")
