import json
import logging
import os

from datasets import DatasetDict
from sqlalchemy import JSON, exc
from sqlalchemy.orm import Session

from DashAI.back.converters.base_converter import BaseConverter
from DashAI.back.database.models import Dataset
from DashAI.back.dataloaders.classes.dashai_dataset import (
    DashAIDataset,
    load_dataset,
    save_dataset,
)
from DashAI.back.job.base_job import BaseJob, JobError

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)


class ConverterJob(BaseJob):
    """ConverterJob class to run the converter application."""
    
    def set_status_as_delivered(self) -> None:
        """Set the status of the job as delivered."""
        pass

    def run(self) -> None:
        from DashAI.back.core.config import component_registry, settings
        dataset_id: int = self.kwargs["dataset_id"]
        db: Session = self.kwargs["db"]
        converter_type_name: str = self.kwargs["converter_type_name"]
        new_dataset_name: str = self.kwargs["new_dataset_name"]
        converter_params: JSON = self.kwargs["converter_params"]

        try:
            # try to get the dataset from the DB
            dataset: Dataset = db.get(Dataset, dataset_id)
            if not dataset:
                raise JobError(f"Dataset {dataset_id} does not exist in DB.")
            # try to load the dataset from the path
            try:
                loaded_dataset: DatasetDict = load_dataset(
                    f"{dataset.file_path}/dataset"
                )
            except Exception as e:
                log.exception(e)
                raise JobError(
                    f"Can not load dataset from path {dataset.file_path}",
                ) from e

            # try to get the converter type from the registry
            try:
                converter_type = component_registry[converter_type_name]["class"]
            except Exception as e:
                log.exception(e)
                raise JobError(
                    f"Unable to find Converter {converter_type_name} in registry",
                ) from e

            # try to instantiate the converter
            try:
                converter: BaseConverter = converter_type(**converter_params)
            except Exception as e:
                log.exception(e)
                raise JobError(
                    f"Unable to instantiate converter {converter_type_name}"
                    f"with params {converter_params}"
                ) from e

            # apply the converter to the dataset
            try:
                converted_dataset: DatasetDict[
                    str, DashAIDataset
                ] = converter.transform(loaded_dataset)
            except Exception as e:
                log.exception(e)
                raise JobError(
                    f"Unable to apply converter {converter_type_name} to dataset"
                    f" {dataset_id}"
                ) from e

            # verify if the new dataset name is not already used in the filesystem
            if os.path.exists(
                os.path.join(settings.USER_DATASET_PATH, f"{new_dataset_name}")
            ):
                raise JobError(
                    f"Dataset {new_dataset_name} already exists in filesystem.",
                )

            # create the new dataset folder
            folder_path = os.path.join(
                settings.USER_DATASET_PATH, f"{new_dataset_name}"
            )
            save_dataset(converted_dataset, os.path.join(folder_path, "dataset"))

            train_split_converted: DashAIDataset = converted_dataset["train"]
            inputs_columns = train_split_converted.inputs_columns

            try:
                folder_path = os.path.realpath(folder_path)
                dataset = Dataset(
                    name=new_dataset_name,
                    feature_names=json.dumps(inputs_columns),
                    file_path=folder_path,
                )
                db.add(dataset)
                db.commit()
                db.refresh(dataset)
                return dataset

            except exc.SQLAlchemyError as e:
                db.rollback()
                raise e

        except Exception as e:
            db.commit()
            raise e
