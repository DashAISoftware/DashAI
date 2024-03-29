"""DashAI CSV Dataloader."""
import os
import shutil
from typing import Any, Dict, Union

from beartype import beartype
from datasets import DatasetDict, load_dataset
from starlette.datastructures import UploadFile

from DashAI.back.dataloaders.classes.dataloader import BaseDataLoader


class CSVDataLoader(BaseDataLoader):
    """Data loader for tabular data in CSV files."""

    COMPATIBLE_COMPONENTS = ["TabularClassificationTask"]

    def _check_params(
        self,
        params: Dict[str, Any],
    ) -> None:
        if "separator" not in params:
            raise ValueError(
                "Error loading CSV file: separator parameter was not provided."
            )
        separator = params["separator"]

        if not isinstance(separator, str):
            raise TypeError(
                f"Param separator should be a string, got {type(params['separator'])}"
            )

    @beartype
    def load_data(
        self,
        filepath_or_buffer: Union[UploadFile, str],
        temp_path: str,
        params: Dict[str, Any],
    ) -> DatasetDict:
        """Load the uploaded CSV files into a DatasetDict.

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
        self._check_params(params)
        separator = params["separator"]

        if isinstance(filepath_or_buffer, str):
            dataset = load_dataset("csv", data_files=filepath_or_buffer, sep=separator)

        elif isinstance(filepath_or_buffer, UploadFile):
            files_path = self.extract_files(temp_path, filepath_or_buffer)
            if files_path.split("/")[-1] == "files":
                try:
                    dataset = load_dataset("csv", data_dir=files_path, sep=separator)
                finally:
                    shutil.rmtree(temp_path, ignore_errors=True)
            else:
                try:
                    dataset = load_dataset("csv", data_files=files_path, sep=separator)
                finally:
                    os.remove(files_path)

        return dataset
