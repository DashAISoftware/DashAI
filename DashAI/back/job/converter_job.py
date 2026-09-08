import logging
from typing import TYPE_CHECKING

from kink import inject
from sqlalchemy import exc

from DashAI.back.api.api_v1.schemas.converter_params import ConverterParams
from DashAI.back.converters.dataset_columns import (
    rebuild_dataset_with_transformed_columns,
)
from DashAI.back.dependencies.database.models import Converter
from DashAI.back.dependencies.database.models import Dataset as DatasetModel
from DashAI.back.job.base_job import BaseJob, JobError

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

        from DashAI.back.dataloaders.classes.dashai_dataset import (
            load_dataset,
            save_dataset,
        )

        session_factory = di["session_factory"]
        component_registry = di["component_registry"]

        def instantiate_converters(
            converter_name: str,
            converter_params: ConverterParams,
        ) -> object:
            # Import the converter
            try:
                converter_constructor = component_registry[converter_name]["class"]
            except KeyError as e:
                log.exception(e)
                raise JobError(
                    f"Error importing converter {converter_name}: {e}"
                ) from e

            # Get parameters or empty dict if none
            converter_parameters = converter_params.get("params", {})

            return converter_constructor(**converter_parameters)

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
                dataset_id = converter.notebook.dataset_id
                dataset = db.get(DatasetModel, dataset_id)

                # dataset to edit
                dataset_path = f"{converter.notebook.file_path}/dataset"
                loaded_dataset = load_dataset(dataset_path)
                params = converter.parameters or {}
                target_column_index = (
                    params["target"].get("idx")
                    if params.get("target") is not None
                    else None
                )

                if not loaded_dataset:
                    raise JobError(f"Dataset with path {dataset_path} not found")

            except exc.SQLAlchemyError as e:
                log.exception(e)
                converter.set_status_as_error()
                db.commit()
                raise JobError("Error loading dataset info") from e

            # Load dataset
            try:
                # Validate target column index
                if target_column_index is not None and (
                    int(target_column_index) < 1
                    or int(target_column_index) > len(loaded_dataset.features)
                ):
                    raise JobError(
                        f"Target column index {target_column_index} is out of bounds"
                    )
            except Exception as e:
                log.exception(e)
                converter.set_status_as_error()
                db.commit()
                raise JobError(f"Cannot load dataset from {dataset_path}") from e

            try:
                # Get stored converter configurations
                converters_stored_info = {converter.converter: converter.parameters}
                dataset_original_columns = loaded_dataset.column_names

                # Sort converters by order
                converters_sorted_list = sorted(
                    converters_stored_info.items(), key=lambda x: x[1]["order"]
                )

                i = 0
                converter_instances = []

                while i < len(converters_sorted_list):
                    converter_name = converters_sorted_list[i][0]
                    converter_params = converters_sorted_list[i][1]
                    # Regular converter
                    converter_instance = instantiate_converters(
                        converter_name,
                        converter_params,
                    )

                    # Get scope or use default
                    scope = converter_params.get("scope", {"columns": [], "rows": []})

                    # Add to instances
                    converter_instances.append(
                        {
                            "name": converter_name,
                            "instance": converter_instance,
                            "scope": scope,
                        }
                    )
                    i += 1

                # Apply each converter in sequence
                total_converters = len(converter_instances)
                for converter_index, converter_info in enumerate(converter_instances):
                    converter_instance = converter_info["instance"]
                    converter_name = converter_info["name"]
                    converter_scope = converter_info["scope"]

                    # Map converter progress onto the 0.2-0.9 band.
                    self.report_progress(
                        0.2 + 0.7 * (converter_index / max(total_converters, 1)),
                        f"Applying {converter_name}",
                    )
                    log.info(f"Applying converter: {converter_name}")

                    columns_scope = [
                        column["idx"] - 1 for column in converter_scope["columns"]
                    ]
                    scope_column_indexes = sorted(set(columns_scope))

                    if not scope_column_indexes:
                        scope_column_indexes = list(range(len(loaded_dataset.features)))

                    scope_column_names = [
                        dataset_original_columns[index]
                        for index in scope_column_indexes
                    ]

                    rows_scope = [row - 1 for row in converter_scope["rows"]]
                    scope_rows_indexes = sorted(set(rows_scope))

                    y_dataset_fit = None
                    target_column_name = None
                    y_full_transform = None
                    if target_column_index is not None:
                        target_column_index_0based = int(target_column_index) - 1
                        target_column_name = dataset_original_columns[
                            target_column_index_0based
                        ]
                        y_dataset_fit = loaded_dataset.select_columns(
                            [target_column_name]
                        )
                        if scope_rows_indexes:
                            y_dataset_fit = y_dataset_fit.select(scope_rows_indexes)
                            y_full_transform = loaded_dataset.select_columns(
                                [target_column_name]
                            )
                        else:
                            y_full_transform = y_dataset_fit

                    X_dataset_fit = loaded_dataset.select_columns(scope_column_names)

                    if scope_rows_indexes:
                        X_dataset_fit = X_dataset_fit.select(scope_rows_indexes)

                    try:
                        converter_instance = converter_instance.fit(
                            X_dataset_fit, y_dataset_fit
                        )
                    except ValueError as e:
                        log.error(f"Validation error in {converter_name}: {e}")
                        raise JobError(
                            f"Validation error fitting {converter_name}: {e}"
                        ) from e
                    except Exception as e:
                        log.exception(e)
                        raise JobError(
                            f"Error fitting converter {converter_name}: {e}"
                        ) from e

                    if scope_rows_indexes:
                        X_full_transform = loaded_dataset.select_columns(
                            scope_column_names
                        )
                    else:
                        # Same reuse as above: no row-level fit scope means
                        # X_dataset_fit already covers the full transform scope.
                        X_full_transform = X_dataset_fit

                    try:
                        transformed_dataset = converter_instance.transform(
                            X_full_transform, y_full_transform
                        )
                    except Exception as e:
                        log.exception(e)
                        raise JobError(
                            f"Error transforming data with {converter_name}: {e}"
                        ) from e

                    if type(converter_instance).CHANGES_ROW_COUNT:
                        loaded_dataset = transformed_dataset
                    else:
                        loaded_dataset = rebuild_dataset_with_transformed_columns(
                            loaded_dataset,
                            transformed_dataset,
                            scope_column_names,
                            scope_column_indexes,
                        )

                    dataset_original_columns = loaded_dataset.column_names

                self.report_progress(0.95, "Saving dataset")
                save_dataset(loaded_dataset, f"{dataset_path}")
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
