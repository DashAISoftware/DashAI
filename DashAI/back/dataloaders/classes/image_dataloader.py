"""DashAI Image Dataloader."""
from typing import Any, Dict, Union

from beartype import beartype
from datasets import DatasetDict, load_dataset
from starlette.datastructures import UploadFile

from DashAI.back.dataloaders.classes.dataloader import BaseDataLoader


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
