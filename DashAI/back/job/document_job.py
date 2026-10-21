"""Job that parses an uploaded or downloaded file into a persistent document."""

import logging
import os
import shutil
import uuid
from contextlib import suppress
from pathlib import Path
from typing import TYPE_CHECKING, Optional
from urllib.parse import unquote

from kink import di, inject
from sqlalchemy import exc

from DashAI.back.dataloaders.classes.document_dataloader import redact_params
from DashAI.back.dependencies.database.models import DataDocument
from DashAI.back.job.base_job import BaseJob, JobError
from DashAI.back.units.context import ExecutionContext
from DashAI.back.units.parse_document_unit import ParseDocumentUnit
from DashAI.back.units.save_document_to_path_unit import SaveDocumentToPathUnit
from DashAI.back.units.store_datafile_document_source_unit import (
    StoreDatafileDocumentSourceUnit,
)
from DashAI.back.units.store_uploaded_document_source_unit import (
    StoreUploadedDocumentSourceUnit,
)

if TYPE_CHECKING:
    from sqlalchemy.orm import sessionmaker

log = logging.getLogger(__name__)


class DocumentJob(BaseJob):
    """Parse a file with a document loader and store the result.

    The ``DataDocument`` row is created beforehand by ``POST /api/v1/documents``
    and already holds the loader name and its validated parameters. The job
    copies the source file to ``<DOCUMENTS_PATH>/<uuid>/source/``, parses it,
    saves the document under ``<uuid>/document/`` and fills the row.

    The source is either an upload or a file inside a completed hub download.
    Each has its own unit to store it, and both publish the same keys, so the
    parsing and saving units are shared.

    Parameters
    ----------
    kwargs : Dict[str, Any]
        ``document_id`` (required) and ``name`` (optional, for the job list).
        Uploads carry ``file_path``, ``temp_dir`` and ``filename``, which
        ``POST /api/v1/job/`` adds for multipart requests. Hub imports carry
        ``datafile_id`` and optionally ``selected_file``, the file inside the
        download relative to its root.
    """

    @inject
    def set_status_as_delivered(
        self, session_factory: "sessionmaker" = lambda di: di["session_factory"]
    ) -> None:
        """Set the status of the document as delivered.

        Raises
        ------
        JobError
            If the row does not exist or cannot be updated.
        """
        document_id = self.kwargs["document_id"]
        with session_factory() as db:
            document = db.get(DataDocument, document_id)
            if document is None:
                raise JobError(f"Document with id {document_id} not found.")
            try:
                document.set_status_as_delivered()
                db.commit()
            except exc.SQLAlchemyError as e:
                log.exception(e)
                raise JobError(
                    "Error while setting the status of the document as delivered."
                ) from e

    @inject
    def set_status_as_error(
        self, session_factory: "sessionmaker" = lambda di: di["session_factory"]
    ) -> None:
        """Set the status of the document as error.

        Raises
        ------
        JobError
            If the row does not exist or cannot be updated.
        """
        document_id = self.kwargs["document_id"]
        with session_factory() as db:
            document = db.get(DataDocument, document_id)
            if document is None:
                raise JobError(f"Document with id {document_id} not found.")
            try:
                document.set_status_as_error()
                db.commit()
            except exc.SQLAlchemyError as e:
                log.exception(e)
                raise JobError(
                    "Error while setting the status of the document as error."
                ) from e

    @inject
    def on_cancel(
        self, session_factory: "sessionmaker" = lambda di: di["session_factory"]
    ) -> None:
        """Remove what a killed job left behind and mark the row as error.

        Failures are logged and never raised again.
        """
        temp_dir = self.kwargs.get("temp_dir")
        if temp_dir:
            shutil.rmtree(temp_dir, ignore_errors=True)

        document_id = self.kwargs.get("document_id")
        if document_id is None:
            return
        try:
            with session_factory() as db:
                document = db.get(DataDocument, document_id)
                if document is None:
                    return
                if document.file_path:
                    shutil.rmtree(document.file_path, ignore_errors=True)
                document.file_path = ""
                document.set_status_as_error()
                db.commit()
        except Exception:
            log.exception(
                f"on_cancel cleanup failed for DocumentJob (document_id={document_id})"
            )

    def get_job_name(self) -> str:
        """Get a descriptive name for the job.

        Returns
        -------
        str
            ``"Document: <name>"`` when a name was passed, else ``"Document load"``.
        """
        name = self.kwargs.get("name")
        return f"Document: {name}" if name else "Document load"

    def _mark_failed(
        self, session_factory: "sessionmaker", folder_path: Optional[Path]
    ) -> None:
        """Delete the partial document folder and set the row to error.

        Parameters
        ----------
        session_factory : sessionmaker
            Session factory from the DI container.
        folder_path : Optional[pathlib.Path]
            The ``<uuid>`` folder created by this run, if any.
        """
        if folder_path is not None:
            shutil.rmtree(folder_path, ignore_errors=True)
        with suppress(Exception), session_factory() as db:
            document = db.get(DataDocument, self.kwargs.get("document_id"))
            if document is not None:
                document.file_path = ""
                document.dataloader_params = redact_params(document.dataloader_params)
                document.set_status_as_error()
                db.commit()

    def run(self) -> None:
        """Store the source file, parse it and fill the document row.

        Raises
        ------
        JobError
            If the source, the row or the loader is missing, or parsing fails.
        """
        session_factory = di["session_factory"]
        config = di["config"]

        document_id = self.kwargs.get("document_id")
        datafile_id = self.kwargs.get("datafile_id")
        upload_path = self.kwargs.get("file_path")
        temp_dir = self.kwargs.get("temp_dir")
        raw_name = self.kwargs.get("filename") or (
            os.path.basename(upload_path) if upload_path else ""
        )
        file_name = os.path.basename(unquote(raw_name))
        folder_path: Optional[Path] = None
        ctx = ExecutionContext()

        try:
            if datafile_id is None:
                if not upload_path or not os.path.isfile(upload_path):
                    raise JobError("No file was uploaded for this document.")
                if not file_name:
                    raise JobError("The uploaded file has no name.")

            with session_factory() as db:
                document = db.get(DataDocument, document_id)
                if document is None:
                    raise JobError(f"Document with id {document_id} not found.")
                dataloader_name = document.dataloader
                dataloader_params = dict(document.dataloader_params or {})
                folder_path = Path(config["DOCUMENTS_PATH"]) / str(uuid.uuid4())
                folder_path.mkdir(parents=True)
                document.file_path = os.path.realpath(folder_path)
                document.huey_id = self.kwargs.get("huey_id")
                document.set_status_as_started()
                db.commit()

            if datafile_id is None:
                store_source = StoreUploadedDocumentSourceUnit(
                    upload_path=upload_path,
                    file_name=file_name,
                    path=str(folder_path / "source"),
                )
            else:
                store_source = StoreDatafileDocumentSourceUnit(
                    datafile_id=datafile_id,
                    selected_file=self.kwargs.get("selected_file"),
                    path=str(folder_path / "source"),
                )
            parse_document = ParseDocumentUnit(
                dataloader={"component": dataloader_name, "params": dataloader_params}
            )
            parse_document.validate(ctx)

            self.report_progress(0.1, "Storing source file")
            store_source(ctx)

            self.report_progress(0.3, "Parsing document")
            parse_document(ctx)

            self.report_progress(0.8, "Saving document")
            SaveDocumentToPathUnit(path=str(folder_path / "document"))(ctx)

            parsed = ctx.require("document")
            source_path = Path(ctx.require("source_path"))
            with session_factory() as db:
                document = db.get(DataDocument, document_id)
                if document is None:
                    raise JobError(
                        f"Document with id {document_id} was deleted while parsing."
                    )
                document.file_name = source_path.name
                document.file_type = source_path.suffix.lower().lstrip(".")
                document.file_hash = ctx.require("file_hash")
                document.content_counts = {
                    content_type.display_name(): parsed.count(content_type)
                    for content_type in parsed.types
                }
                document.total_pages = parsed.metadata.get("n_pages")
                document.dataloader_params = redact_params(dataloader_params)
                document.set_status_as_finished()
                db.commit()
        except JobError as e:
            log.error(f"Document creation failed: {e}")
            self._mark_failed(session_factory, folder_path)
            raise
        except Exception as e:
            log.exception(e)
            self._mark_failed(session_factory, folder_path)
            raise JobError(f"Error loading document: {e}") from e
        finally:
            ctx.clear_cache()
            if temp_dir and os.path.exists(temp_dir):
                shutil.rmtree(temp_dir, ignore_errors=True)
