import logging
from typing import TYPE_CHECKING

from kink import inject
from sqlalchemy import exc

from DashAI.back.converters.converter_report import save_converter_report
from DashAI.back.core.data_kinds import DOCUMENT
from DashAI.back.dependencies.database.models import Converter
from DashAI.back.dependencies.database.models import Dataset as DatasetModel
from DashAI.back.job.base_job import BaseJob, JobError
from DashAI.back.units.apply_converter_unit import ApplyConverterUnit
from DashAI.back.units.context import ExecutionContext
from DashAI.back.units.load_dataset_unit import LoadDatasetUnit
from DashAI.back.units.save_dataset_unit import SaveDatasetUnit

if TYPE_CHECKING:
    from sqlalchemy.orm import sessionmaker

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)


class ConverterJob(BaseJob):
    """ConverterJob class to modify a dataset by applying a
    sequence of converters."""

    @inject
    def set_status_as_delivered(
        self, session_factory: "sessionmaker" = lambda di: di["session_factory"]
    ) -> None:
        """Set the status of the converter as delivered."""
        converter_id = self.kwargs["converter_id"]

        with session_factory() as db:
            converter = db.get(Converter, converter_id)
            if converter is None:
                raise JobError(
                    f"Converter with id {converter_id} does not exist in DB."
                )

            try:
                converter.set_status_as_delivered()
                db.commit()
            except exc.SQLAlchemyError as e:
                log.exception(e)
                raise JobError("Error setting converter status as delivered") from e

    @inject
    def set_status_as_error(
        self, session_factory: "sessionmaker" = lambda di: di["session_factory"]
    ) -> None:
        """Set the status of the converter as error."""
        converter_id = self.kwargs.get("converter_id")
        if converter_id is None:
            return

        with session_factory() as db:
            converter = db.get(Converter, converter_id)
            if converter is None:
                return

            try:
                converter.set_status_as_error()
                db.commit()
            except exc.SQLAlchemyError as e:
                log.exception(e)

    @inject
    def get_job_name(self) -> str:
        """Get a descriptive name for the job."""
        converter_id = self.kwargs.get("converter_id")
        if not converter_id:
            return "Converter Job"

        from kink import di

        session_factory = di["session_factory"]

        try:
            with session_factory() as db:
                converter = db.get(Converter, converter_id)
                if not converter:
                    return f"Converter Job #{converter_id}"
                converter_name = converter.converter

                notebook = converter.notebook
                if notebook is not None and notebook.data_kind == DOCUMENT:
                    if notebook.document is not None and notebook.document.name:
                        return f"{converter_name}: {notebook.document.name}"
                elif notebook is not None:
                    dataset = db.get(DatasetModel, notebook.dataset_id)
                    if dataset and dataset.name:
                        return f"{converter_name}: {dataset.name}"

                return f"{converter_name}"
        except Exception as e:
            log.exception(f"Error getting job name: {e}")

        return f"Converter Job #{converter_id}"

    @inject
    def run(
        self,
    ) -> None:
        from kink import di

        session_factory = di["session_factory"]

        ctx = ExecutionContext()

        # Extract job parameters
        converter_id = self.kwargs["converter_id"]
        with session_factory() as db:
            # Validate input parameters
            try:
                if converter_id is None:
                    raise JobError("Converter ID is required")

                converter: Converter = db.get(Converter, converter_id)
                if not converter:
                    raise JobError(f"Converter with id {converter_id} not found")

                converter.set_status_as_started()
                db.commit()
            except exc.SQLAlchemyError as e:
                log.exception(e)
                raise JobError("Error loading converter info") from e

            if converter.notebook.data_kind == DOCUMENT:
                registry = di["component_registry"]
                converter_params = (converter.parameters or {}).get("params") or {}
                self._run_on_document(
                    db,
                    converter,
                    lambda: registry[converter.converter]["class"](**converter_params),
                )
                return

            self.report_progress(0.1, "Loading dataset")

            # Get dataset
            try:
                notebook_id = converter.notebook_id
                dataset_id = converter.notebook.dataset_id
                dataset = db.get(DatasetModel, dataset_id)

                # dataset to edit: the notebook's own working copy
                LoadDatasetUnit(notebook_id=notebook_id)(ctx)
                dataset_path = ctx.require("dataset_path")

                # How the converter configuration is stored on the row, not
                # part of the transformation itself.
                params = converter.parameters or {}

            except exc.SQLAlchemyError as e:
                log.exception(e)
                converter.set_status_as_error()
                db.commit()
                raise JobError("Error loading dataset info") from e
            except Exception:
                # Anything the load unit raises (missing notebook, unreadable
                # dataset) also has to leave the row in ERROR. Nothing marks it
                # otherwise: the Huey error signal only writes to its own
                # task_copy table, never to the Converter row, so without this
                # the converter would stay STARTED forever. Re-raised as-is so
                # the unit's specific message survives.
                converter.set_status_as_error()
                db.commit()
                raise

            apply_converter = ApplyConverterUnit(
                converter={
                    "component": converter.converter,
                    "params": params.get("params") or {},
                },
                scope=params.get("scope"),
                target=params.get("target"),
            )

            # Validating before the work starts keeps an impossible target
            # index reported as a dataset problem, which is where it was
            # reported before the job was split into units.
            try:
                apply_converter.validate(ctx)
            except Exception as e:
                log.exception(e)
                converter.set_status_as_error()
                db.commit()
                raise JobError(f"Cannot load dataset from {dataset_path}") from e

            try:
                self.report_progress(0.2, f"Applying {converter.converter}")
                apply_converter(ctx)

                # A converter may describe its own fit (Clustering does), and
                # the explorers that read that description find it next to the
                # notebook. Asked of the instance the unit fitted, so the report
                # is about the fit that produced the dataset being saved. The
                # paths are read only then: a converter that describes nothing
                # needs none, and every other converter runs as it did before.
                report = ctx.require("fitted_converter").get_report()
                if report is not None:
                    notebook_root = di["config"]["NOTEBOOK_PATH"]
                    save_converter_report(
                        notebook_path=notebook_root / str(notebook_id),
                        converter_id=converter.id,
                        report=report,
                    )

                self.report_progress(0.95, "Saving dataset")
                SaveDatasetUnit()(ctx)
                converter.set_status_as_finished()
                db.commit()
                db.refresh(dataset)

            except Exception as e:
                log.exception(e)
                converter.set_status_as_error()
                db.commit()
                raise JobError(
                    f"Error applying converters to dataset {dataset_id}: {e}"
                ) from e
            finally:
                ctx.clear_cache()

    def _run_on_document(self, db, converter: Converter, make_converter) -> None:
        """Apply a converter to the document items selected in its scope.

        The working copy is saved only when every selected content type
        converted cleanly, so a refused result leaves the document as it was.

        Parameters
        ----------
        db : Session
            The open session holding ``converter``.
        converter : Converter
            The converter record, already marked as started.
        make_converter : Callable[[], object]
            Returns a new configured converter instance.

        Raises
        ------
        JobError
            If the document cannot be loaded, converted or saved.
        """
        from DashAI.back.dataloaders.classes.dashai_document import (
            load_document,
            save_document,
        )
        from DashAI.back.dataloaders.classes.document_items import (
            apply_converter_to_document,
            selection_from_columns,
        )
        from DashAI.back.dataloaders.classes.notebook_data import notebook_data_path

        document_path = notebook_data_path(converter.notebook)
        try:
            self.report_progress(0.1, "Loading document")
            document = load_document(document_path)
            scope = (converter.parameters or {}).get("scope") or {}
            selection = selection_from_columns(scope.get("columns") or [])
            self.report_progress(0.3, f"Applying {converter.converter}")
            document = apply_converter_to_document(document, make_converter, selection)
            self.report_progress(0.95, "Saving document")
            save_document(document, document_path)
            converter.set_status_as_finished()
            db.commit()
        except Exception as e:
            log.exception(e)
            converter.set_status_as_error()
            db.commit()
            raise JobError(
                f"Error applying {converter.converter} to the document: {e}"
            ) from e
