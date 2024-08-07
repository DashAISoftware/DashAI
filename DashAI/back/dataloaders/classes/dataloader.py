"""DashAI base class for dataloaders."""

import io
import logging
import zipfile
from abc import abstractmethod
from typing import Any, Dict, Final, Union

from datasets import DatasetDict
from starlette.datastructures import UploadFile

from DashAI.back.config_object import ConfigObject
from DashAI.back.core.schema_fields import (
    bool_field,
    float_field,
    int_field,
    schema_field,
)
from DashAI.back.core.schema_fields.base_schema import BaseSchema

logger = logging.getLogger(__name__)


class DatasetSplitsSchema(BaseSchema):
    train_size: schema_field(
        float_field(ge=0.0, le=1.0),
        0.7,
        (
            "The training set contains the data to be used for training a model. "
            "Must be defined between 0 and 100% of the data."
        ),
    )  # type: ignore
    test_size: schema_field(
        float_field(ge=0.0, le=1.0),
        0.2,
        (
            "The test set contains the data that will be used to evaluate a model. "
            "Must be defined between 0 and 100% of the data."
        ),
    )  # type: ignore
    val_size: schema_field(
        float_field(ge=0.0, le=1.0),
        0.1,
        (
            "The validation set contains the data to be used to validate a model. "
            "Must be defined between 0 and 100% of the data."
        ),
    )  # type: ignore


class DataloaderMoreOptionsSchema(BaseSchema):
    shuffle: schema_field(
        bool_field(),
        True,
        (
            "Determines whether the data will be shuffle when defining the sets or "
            "not. It must be true for shuffle the data, otherwise false."
        ),
    )  # type: ignore
    seed: schema_field(
        int_field(ge=0),
        0,
        (
            "A seed defines a value with which the same mixture of data will always "
            "be obtained. It must be an integer greater than or equal to 0."
        ),
    )  # type: ignore
    stratify: schema_field(
        bool_field(),
        False,
        (
            "Defines whether the data will be proportionally separated according to "
            "the distribution of classes in each set."
        ),
    )  # type: ignore


class BaseDataLoader(ConfigObject):
    """Abstract class with base methods for DashAI dataloaders."""

    TYPE: Final[str] = "DataLoader"

    @abstractmethod
    def load_data(
        self,
        filepath_or_buffer: Union[UploadFile, str],
        temp_path: str,
        params: Dict[str, Any],
    ) -> DatasetDict:
        """Load data abstract method.

        Parameters
        ----------
        filepath_or_buffer : Union[UploadFile, str], optional
            An URL where the dataset is located or a FastAPI/Uvicorn uploaded file
            object.
        temp_path : str
            The temporary path where the files will be extracted and then uploaded.
        params : Dict[str, Any]
            Dict with the dataloader parameters.

        Returns
        -------
        DatasetDict
            A HuggingFace's Dataset with the loaded data.
        """
        raise NotImplementedError

    def extract_files(self, dataset_path: str, file: UploadFile) -> str:
        """Extract the files to load the data in a DataDict later.

        Args:
            dataset_path (str): Path where dataset will be saved.
            file (UploadFile): File uploaded for the user.

        Returns
        -------
            str: Path of the files extracted.
        """
        if file.content_type == "application/zip":
            files_path = f"{dataset_path}/files"
            with zipfile.ZipFile(
                file=io.BytesIO(file.file.read()),
                mode="r",
            ) as zip_file:
                zip_file.extractall(path=files_path)
        else:
            files_path = f"{dataset_path}/{file.filename}"
            with open(files_path, "wb") as f:
                f.write(file.file.read())
        return files_path
