"""DashAI Image Dataloader."""

from typing import Any, Dict, Union

from beartype import beartype
from datasets import DatasetDict, load_dataset
from starlette.datastructures import UploadFile

from DashAI.back.core.schema_fields import (
    bool_field,
    none_type,
    schema_field,
    string_field,
)
from DashAI.back.core.schema_fields.base_schema import BaseSchema
from DashAI.back.dataloaders.classes.dataloader import (
    BaseDataLoader,
    DataloaderMoreOptionsSchema,
    DatasetSplitsSchema,
)


class ImageDataloaderSchema(BaseSchema):
    name: schema_field(
        none_type(string_field()),
        "",
        (
            "Custom name to register your dataset. If no name is specified, "
            "the name of the uploaded file will be used."
        ),
    )  # type: ignore
    splits_in_folders: schema_field(
        bool_field(),
        False,
        (
            "If your data has folders that define the splits select 'true', "
            "otherwise 'false'."
        ),
    )  # type: ignore
    splits: DatasetSplitsSchema
    more_options: DataloaderMoreOptionsSchema


class ImageDataLoader(BaseDataLoader):
    """Data loader for data from image files."""

    COMPATIBLE_COMPONENTS = ["ImageClassificationTask"]
    SCHEMA = ImageDataloaderSchema

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
            dataset = load_dataset("imagefolder", data_dir=filepath_or_buffer)
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
