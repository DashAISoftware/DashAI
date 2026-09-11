import logging
from contextlib import suppress
from typing import TYPE_CHECKING

from kink import di, inject
from sqlalchemy import exc

from DashAI.back.api.api_v1.schemas.datasets_params import DatasetParams
from DashAI.back.api.utils import parse_params
from DashAI.back.dependencies.database.models import Converter, Dataset, Notebook
from DashAI.back.job.base_job import BaseJob, JobError
from DashAI.back.units.apply_dataset_schema_unit import ApplyDatasetSchemaUnit
from DashAI.back.units.compute_dataset_metadata_unit import ComputeDatasetMetadataUnit
from DashAI.back.units.context import ExecutionContext
from DashAI.back.units.infer_dataset_types_unit import InferDatasetTypesUnit
from DashAI.back.units.load_datafile_dataset_unit import LoadDatafileDatasetUnit
from DashAI.back.units.load_dataset_unit import LoadDatasetUnit
from DashAI.back.units.load_uploaded_dataset_unit import LoadUploadedDatasetUnit
from DashAI.back.units.save_dataset_to_path_unit import SaveDatasetToPathUnit

if TYPE_CHECKING:
    from sqlalchemy.orm import sessionmaker


log = logging.getLogger(__name__)


class DatasetJob(BaseJob):
    """
    Job for processing and uploading datasets using streaming data processing.

    Parameters
    ----------
    kwargs : Dict[str, Any]
        A dictionary containing the parameters for the job, including:
        - name: Name of the dataset
        - datatype_name: Name of the datatype
        - params: Parameters for the datatype
        - file_path: Path to the temporarily saved file
        - temp_dir: Directory containing the temporary file
        - filename: Name of the uploaded file
        - db: Database session
    """

    @inject
    def set_status_as_delivered(
        self, session_factory: "sessionmaker" = lambda di: di["session_factory"]
    ) -> None:
        """Set the status of the dataset as delivered."""
        dataset_id: int = self.kwargs["dataset_id"]
        with session_factory() as db:
            dataset: Dataset = db.get(Dataset, dataset_id)

            if dataset is None:
                raise JobError(f"Dataset with id {dataset_id} not found.")

            try:
                dataset.set_status_as_delivered()
                db.commit()
            except exc.SQLAlchemyError as e:
                log.exception(e)
                raise JobError(
                    "Error while setting the status of the dataset as delivered."
                ) from e

    @inject
    def set_status_as_error(
        self, session_factory: "sessionmaker" = lambda di: di["session_factory"]
    ) -> None:
        """Set the job status as error."""
        dataset_id: int = self.kwargs["dataset_id"]
        with session_factory() as db:
            dataset: Dataset = db.get(Dataset, dataset_id)

            if dataset is None:
                raise JobError(f"Dataset with id {dataset_id} not found.")

            try:
                dataset.set_status_as_error()
                db.commit()
            except exc.SQLAlchemyError as e:
                log.exception(e)
                raise JobError(
                    "Error while setting the status of the dataset as error."
                ) from e

    @inject
    def on_cancel(
        self, session_factory: "sessionmaker" = lambda di: di["session_factory"]
    ) -> None:
        """Delete all artifacts produced by a cancelled DatasetJob.

        The dataset was never successfully saved, so:
        - Any partially-written dataset directory is removed from disk.
        - The temp upload directory is removed.
        - The Dataset DB record is deleted entirely so it no longer appears in the UI.
        """
        import shutil

        dataset_id: int = self.kwargs.get("dataset_id")
        temp_dir = self.kwargs.get("temp_dir")

        # Clean up temp upload directory
        if temp_dir:
            with suppress(Exception):
                shutil.rmtree(temp_dir, ignore_errors=True)

        if dataset_id is None:
            return

        try:
            with session_factory() as db:
                from DashAI.back.dependencies.database.models import Dataset

                dataset = db.get(Dataset, dataset_id)
                if dataset is None:
                    return

                # Delete the partially-written dataset directory if it exists
                file_path = dataset.file_path or ""
                if file_path:
                    with suppress(Exception):
                        shutil.rmtree(file_path, ignore_errors=True)

                # Delete the record — it was never a valid dataset
                db.delete(dataset)
                db.commit()

        except Exception:
            log.exception(
                f"on_cancel cleanup failed for DatasetJob (dataset_id={dataset_id})"
            )

    def get_job_name(self) -> str:
        """Get a descriptive name for the job."""
        name = self.kwargs.get("name", "")
        if name:
            return f"Dataset: {name}"

        params = self.kwargs.get("params", {})
        if params and isinstance(params, dict) and "name" in params:
            return f"Dataset: {params['name']}"
        return "Dataset load"

    @inject
    def run(
        self,
    ) -> None:
        import gc
        import json
        import os
        import shutil
        import tempfile
        import uuid
        from pathlib import Path

        session_factory = di["session_factory"]
        config = di["config"]

        dataset_id = self.kwargs.get("dataset_id")
        notebook_id = self.kwargs.get("notebook_id", None)
        params = self.kwargs.get("params", {})
        n_sample = self.kwargs.get("n_sample", None)
        file_path = self.kwargs.get("file_path")
        temp_dir = self.kwargs.get("temp_dir")
        if not temp_dir:
            # The dataloaders forward this path to HuggingFace as ``cache_dir``.
            # Passing it along unset would stringify to "None" and create a
            # directory literally named "None" in the working directory.
            temp_dir = tempfile.mkdtemp(prefix="dashai-dataset-")
        url = self.kwargs.get("url", "")

        ctx = ExecutionContext()

        # Whether the destination folder is this job's to delete. Re-importing
        # into an existing dataset writes over its current folder, and the
        # failure paths below clean up by removing it — which would destroy data
        # the surviving row still points at. Only a folder this run created may
        # be removed.
        #
        # Bound before the try, not inside it: the handler at the bottom reads
        # it, and a failure raised before the assignment would otherwise reach
        # that handler with the name unbound.
        folder_is_ours = False

        try:
            with session_factory() as db:
                dataset = db.get(Dataset, dataset_id)
                if not dataset:
                    raise JobError(f"Dataset with ID {dataset_id} not found.")

                dataset.set_status_as_started()
                db.commit()
                db.refresh(dataset)

            self.report_progress(0.1, "Loading data")

            if n_sample and dataset.file_path != "":
                folder_path = Path(dataset.file_path)
            else:
                random_name = str(uuid.uuid4())
                folder_path: Path = config["DATASETS_PATH"] / random_name

                try:
                    log.debug("Trying to create a new dataset path: %s", folder_path)
                    folder_path.mkdir(parents=True)
                except FileExistsError as e:
                    log.exception(e)
                    raise JobError(
                        f"A dataset with the name {random_name} already exists."
                    ) from e
                folder_is_ours = True

                # Write folder_path to DB immediately so on_cancel can delete it
                # even if the job is killed before the final commit.
                with session_factory() as db:
                    _d = db.get(Dataset, dataset_id)
                    if _d is not None:
                        _d.file_path = str(os.path.realpath(folder_path))
                        db.commit()

            from_notebook_no_converters = False
            try:
                if notebook_id is not None:
                    log.debug(f"Copying dataset from notebook id {notebook_id}.")
                    with session_factory() as db:
                        notebook_dataset = (
                            db.query(Notebook)
                            .filter(Notebook.id == notebook_id)
                            .first()
                        )
                        # Checked here rather than left to the load unit, whose
                        # own wording for a missing notebook differs from this
                        # one. The message reaches the UI, so it is preserved.
                        if not notebook_dataset:
                            msg = (
                                "Notebook with ID "
                                f"{notebook_id}"
                                " has no associated dataset."
                            )
                            raise JobError(msg)
                        # Detect whether any converters have been applied to
                        # this notebook. When none, the saved data is byte-
                        # identical to the source dataset, so we can reuse
                        # the source's metadata directly instead of
                        # recomputing.
                        has_converters = (
                            db.query(Converter)
                            .filter(Converter.notebook_id == notebook_id)
                            .first()
                            is not None
                        )
                        from_notebook_no_converters = not has_converters

                    # ``LoadDatasetUnit`` also publishes ``dataset_path`` (the
                    # notebook's own copy) and ``dataset_id`` (the *source*
                    # dataset). Neither describes what is being created here: the
                    # save goes to a new folder, and this job's ``dataset_id`` is
                    # the destination row, read from kwargs. Nothing below reads
                    # them from the context, and nothing should start to.
                    LoadDatasetUnit(notebook_id=notebook_id)(ctx)

                    # No schema is applied to a notebook copy: it is already a
                    # stored dataset, with its types settled when it was created.

                else:
                    source_name = self.kwargs.get("source_name")

                    if source_name:
                        # --- Hub import path ---
                        # The id is required, and it is the request that is
                        # malformed without it, so the check stays here rather
                        # than becoming a unit that cannot be configured.
                        datafile_id = params.get("datafile_id")
                        if datafile_id is None:
                            raise JobError("datafile_id is required for hub imports.")

                        LoadDatafileDatasetUnit(
                            dataloader={
                                "component": params.get("dataloader", ""),
                                "params": params.get("dataloader_params", {}),
                            },
                            datafile_id=datafile_id,
                            selected_file=params.get("selected_file"),
                        )(ctx)
                    else:
                        # --- File / URL upload path ---
                        # Validating the request's params is unpacking of how the
                        # upload arrived, not part of reading the data: the unit
                        # gets the reader already picked and its params already
                        # checked. ``model_dump()`` keeps the payload the reader
                        # receives exactly as it was.
                        parsed_params = parse_params(DatasetParams, json.dumps(params))
                        log.debug("Storing dataset in %s", folder_path)
                        LoadUploadedDatasetUnit(
                            dataloader={
                                "component": parsed_params.dataloader,
                                "params": parsed_params.model_dump(),
                            },
                            source=str(file_path) if file_path is not None else url,
                            temp_path=str(temp_dir),
                            n_sample=n_sample,
                        )(ctx)

                    # The types either come with the request or are worked out
                    # from the data. Both paths end in the same context key, so
                    # the unit that applies them has a single input either way.
                    if params.get("inferred_types"):
                        ctx.put_ref("inferred_types", params["inferred_types"])
                    else:
                        InferDatasetTypesUnit(method="DashAIPtype")(ctx)

                    ApplyDatasetSchemaUnit(
                        column_renames=params.get("column_renames"),
                    )(ctx)

                self.report_progress(0.5, "Computing metadata")

                # ``from_notebook_no_converters`` means the saved data matches
                # the source dataset byte-for-byte, so the metadata it arrived
                # with still describes it. That is a policy decision this job
                # makes from the notebook's converter history; the unit only
                # needs the answer.
                ComputeDatasetMetadataUnit(
                    compute_metadata=params.get("compute_metadata", True),
                    trust_inherited_metadata=from_notebook_no_converters,
                )(ctx)
                gc.collect()

                self.report_progress(0.8, "Saving dataset")

                dataset_save_path = folder_path / "dataset"
                log.debug("Saving dataset in %s", str(dataset_save_path))
                SaveDatasetToPathUnit(path=str(dataset_save_path))(ctx)
            except Exception as e:
                log.exception(e)
                if folder_is_ours:
                    shutil.rmtree(folder_path, ignore_errors=True)
                raise JobError(f"Error loading dataset: {str(e)}") from e

            # Add dataset to database. The counts are read back off the dataset
            # rather than published by the metadata unit: they describe the
            # dataset as it is right now, and a key holding them would go stale
            # the moment anything else transformed it.
            stored_metadata = ctx.require("dataset").splits
            with session_factory() as db:
                log.debug("Storing dataset metadata in database.")
                try:
                    folder_path = os.path.realpath(folder_path)
                    dataset = db.get(Dataset, dataset_id)
                    # Re-read, so it can be gone by now: the row is deletable
                    # through the API while the job runs. Without this guard the
                    # assignment below raises AttributeError on None, and the
                    # data just written to disk is orphaned.
                    if dataset is None:
                        raise JobError(
                            f"Dataset with ID {dataset_id} no longer exists."
                        )
                    dataset.file_path = folder_path
                    dataset.total_rows = stored_metadata.get("total_rows")
                    dataset.total_columns = len(stored_metadata.get("column_names", []))
                    dataset.set_status_as_finished()
                    db.commit()
                    db.refresh(dataset)

                except exc.SQLAlchemyError as e:
                    log.exception(e)
                    if folder_is_ours:
                        shutil.rmtree(folder_path, ignore_errors=True)
                    raise JobError("Internal database error") from e
                except Exception:
                    # Anything else here leaves a dataset on disk that no row
                    # points at, so it has to be cleaned up too. Re-raised
                    # unchanged; the handler below writes the status.
                    if folder_is_ours:
                        shutil.rmtree(folder_path, ignore_errors=True)
                    raise

            log.debug("Dataset creation successfully finished.")

        except Exception as e:
            # Every failure, not just ``JobError``. Nothing else moves this row
            # out of STARTED: Huey's error signal writes to its own ``task_copy``
            # table and never touches ``Dataset``, so an exception this handler
            # does not see leaves the dataset stuck as in-progress forever, and
            # the UI keeps showing a spinner for work that already died.
            log.error(f"Dataset creation failed: {e}")
            try:
                with session_factory() as db:
                    dataset = db.get(Dataset, dataset_id)
                    if dataset:
                        dataset.set_status_as_error()
                        # The path is written to the row as soon as the folder
                        # is created, so a cancelled job can find it and delete
                        # it. The failure paths above already deleted it, so
                        # leaving the path behind would point the row at a
                        # folder that is gone -- and the next re-import would
                        # take it for a folder it may reuse.
                        #
                        # Only a folder this run created: a re-import that
                        # failed leaves the previous one in place, and the row
                        # still points at real data.
                        if folder_is_ours:
                            dataset.file_path = ""
                        db.commit()
                        db.refresh(dataset)
            except Exception as bookkeeping_error:
                # Never let the bookkeeping mask what actually went wrong.
                log.exception(bookkeeping_error)
            # Re-raised as-is: the message is the contract, and wrapping it here
            # would change what every branch above reports.
            raise

        finally:
            ctx.clear_cache()
            gc.collect()
            if temp_dir and os.path.exists(temp_dir):
                try:
                    shutil.rmtree(temp_dir, ignore_errors=True)
                except Exception as e:
                    log.exception(f"Error cleaning up temporary directory: {e}")
