"""DashAI base class for dataloaders."""
import io
import json
import logging
import os
import zipfile
from abc import abstractmethod
from typing import Any, Dict, Final, Union

from datasets import DatasetDict
from starlette.datastructures import UploadFile

from DashAI.back.config_object import ConfigObject

logger = logging.getLogger(__name__)


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

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        """Load the JSON schema asocciated to the dataloader."""
        try:
            dir_path = os.path.dirname(os.path.realpath(__file__))
            parent_dir = os.path.dirname(dir_path)
            with open(
                f"{parent_dir}/description_schemas/{cls.__name__}.json",
            ) as f:
                schema = json.load(f)
            return schema

        except FileNotFoundError:
            logger.exception(
                f"Could not load the schema for {cls.__name__} : File DashAI/back"
                f"/dataloaders/description_schemas/{cls.__name__}.json not found.",
            )
            return {}

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
            with zipfile.ZipFile(io.BytesIO(file.file.read()), "r") as zip_file:
                zip_file.extractall(path=files_path)
        else:
            files_path = f"{dataset_path}/{file.filename}"
            with open(files_path, "wb") as f:
                f.write(file.file.read())
        return files_path
