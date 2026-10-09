import logging
from typing import TYPE_CHECKING

from kink import inject
from sqlalchemy import exc

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

                if hasattr(converter, "notebook") and converter.notebook:
                    dataset = db.get(DatasetModel, converter.notebook.dataset_id)
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
