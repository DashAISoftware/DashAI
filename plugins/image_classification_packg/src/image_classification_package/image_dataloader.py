"""DashAI Image Dataloader."""

import json
import logging
import os
from typing import Any, Dict, Union

from beartype import beartype
from datasets import DatasetDict, load_dataset
from starlette.datastructures import UploadFile

from DashAI.back.dataloaders.classes.dataloader import BaseDataLoader

logger = logging.getLogger(__name__)


class ImageDataLoader(BaseDataLoader):
    """Data loader for data from image files."""

    COMPATIBLE_COMPONENTS = ["ImageClassificationTask"]

    @beartype
    def load_data(
        self,
        filepath_or_buffer: Union[UploadFile, str],
        temp_path: str,
        params: Dict[str, Any],
    ) -> DatasetDict:
        """Load an image dataset.

        Parameters
        ----------
        filepath_or_buffer : Union[UploadFile, str], optional
            An URL where the dataset is located or a FastAPI/Uvicorn uploaded file
            object.
        temp_path : str
            The temporary path where the files will be extracted and then uploaded.
        params : Dict[str, Any]
            Dict with the dataloader parameters. The options are:
            - `separator` (str): The character that delimits the CSV data.

        Returns
        -------
        DatasetDict
            A HuggingFace's Dataset with the loaded data.
        """
        if isinstance(filepath_or_buffer, str):
            dataset = load_dataset("imagefolder", data_files=filepath_or_buffer)
        elif isinstance(filepath_or_buffer, UploadFile):
            if filepath_or_buffer.content_type == "application/zip":
                extracted_files_path = self.extract_files(temp_path, filepath_or_buffer)
                dataset = load_dataset(
                    "imagefolder",
                    data_dir=extracted_files_path,
                )
            else:
                raise Exception(
                    "The image dataloader requires the input file to be a zip file. "
                    f"The following content type was delivered: "
                    f"{filepath_or_buffer.content_type}"
                )

        return dataset

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        """Load the JSON schema asocciated to the dataloader."""
        try:
            # path es la carpeta donde está este archivo
            path = os.path.dirname(os.path.realpath(__file__))
            with open(
                os.path.join(path, "ImageDataLoader.json"),
            ) as f:
                schema = json.load(f)
            return schema

        except FileNotFoundError:
            logger.exception(
                f"Could not load the schema for {cls.__name__} : File DashAI/back"
                f"/dataloaders/description_schemas/{cls.__name__}.json not found.",
            )
            return {}

    @staticmethod
    def get_squema(type, name):
        try:
            # path es la carpeta donde está este archivo
            path = os.path.dirname(os.path.realpath(__file__))
            with open(
                os.path.join(path, "image_dataloader.json"),
            ) as f:
                return json.load(f)

        except FileNotFoundError:
            with open(os.path.join(path, "image_dataloader.json")):
                return json.load(f)
