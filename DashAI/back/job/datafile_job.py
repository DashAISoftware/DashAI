"""Job for downloading a dataset from an external hub source."""

import logging
from pathlib import Path
from typing import TYPE_CHECKING

from kink import di, inject
from sqlalchemy import exc

from DashAI.back.core.enums.status import DatafileStatus
from DashAI.back.dependencies.database.models import Datafile
from DashAI.back.job.base_job import BaseJob, JobError

if TYPE_CHECKING:
    from sqlalchemy.orm import sessionmaker

log = logging.getLogger(__name__)


class DatafileJob(BaseJob):
    """Job that fetches a dataset file from an external hub source.

    Parameters
    ----------
    kwargs : dict
        - datafile_id: int (DB row id)
        - source_name: str (DatasetSource class name)
        - dataset_source_id: str (source-specific dataset identifier)
    """

    @inject
    def set_status_as_delivered(
        self, session_factory: "sessionmaker" = lambda di: di["session_factory"]
    ) -> None:
        """No-op: datafile downloads don't use the delivered state."""

    @inject
    def set_status_as_error(
        self, session_factory: "sessionmaker" = lambda di: di["session_factory"]
    ) -> None:
        datafile_id: int = self.kwargs["datafile_id"]
        error_msg: str = self.kwargs.get("_error_message", "")
        with session_factory() as db:
            row: Datafile = db.get(Datafile, datafile_id)
            if row is not None:
                row.status = DatafileStatus.ERROR
                row.error_message = error_msg
                try:
                    db.commit()
                except exc.SQLAlchemyError as e:
                    log.exception(e)

    def get_job_name(self) -> str:
        return f"Hub download: {self.kwargs.get('dataset_source_id', '')}"

    @inject
    def run(self) -> None:
        import shutil

        component_registry = di["component_registry"]
        session_factory = di["session_factory"]
        config = di["config"]

        datafile_id: int = self.kwargs["datafile_id"]
        source_name: str = self.kwargs["source_name"]
        dataset_source_id: str = self.kwargs["dataset_source_id"]

        download_dir: Path = config["DATAFILE_PATH"] / str(datafile_id)

        try:
            sources = component_registry._registry.get("DatasetSource", {})
            if source_name not in sources:
                raise JobError(f"DatasetSource '{source_name}' not found in registry.")

            download_dir.mkdir(parents=True, exist_ok=True)
            source = sources[source_name]["class"]()
            file_path = source.download_dataset(dataset_source_id, str(download_dir))
            log.debug("Hub dataset '%s' downloaded to %s", dataset_source_id, file_path)

            with session_factory() as db:
                row: Datafile = db.get(Datafile, datafile_id)
                if row is None:
                    raise JobError(f"Datafile row {datafile_id} not found.")
                row.status = DatafileStatus.READY
                row.local_path = str(download_dir)
                size_bytes = sum(
                    f.stat().st_size for f in download_dir.rglob("*") if f.is_file()
                )
                row.size_bytes = size_bytes
                try:
                    db.commit()
                except exc.SQLAlchemyError as e:
                    log.exception(e)
                    raise JobError("DB error saving download path.") from e

            log.debug("Datafile download job %d completed.", datafile_id)

        except Exception as e:
            err_msg = str(e)
            log.error("Datafile download job %d failed: %s", datafile_id, err_msg)
            self.kwargs["_error_message"] = err_msg
            self.set_status_as_error()
            if download_dir.exists():
                shutil.rmtree(download_dir, ignore_errors=True)
            if isinstance(e, JobError):
                raise
            raise JobError(err_msg) from e
