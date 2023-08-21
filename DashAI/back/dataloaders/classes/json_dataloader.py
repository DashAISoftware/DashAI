"""DashAI JSON Dataloader."""
import os
import shutil
from typing import Any, Dict, Union

from beartype import beartype
from datasets import DatasetDict, load_dataset
from starlette.datastructures import UploadFile

from DashAI.back.dataloaders.classes.dataloader import BaseDataLoader


class JSONDataLoader(BaseDataLoader):
    """Data loader for tabular data in JSON files."""

    COMPATIBLE_COMPONENTS = [
        "TabularClassificationTask",
        "TextClassificationTask",
        "TranslationTask",
    ]

    def _check_params(self, params: Dict[str, Any]) -> None:
        if "data_key" not in params:
            raise ValueError(
                "Error loading JSON file: data_key parameter was not provided."
            )

        if not isinstance(params["data_key"], str):
            raise TypeError(
                "params['data_key'] should be a string, "
                f"got {type(params['data_key'])}"
            )

    @beartype
    def load_data(
        self,
        file: Union[UploadFile, str],
        temp_path: str,
        params: Dict[str, Any],
    ) -> DatasetDict:
        """Load the uploaded JSON dataset into a DatasetDict.

        Parameters
        ----------
        file : Union[UploadFile, str], optional
            An URL where the dataset is located or a FastAPI/Uvicorn uploaded file
            object.
        temp_path : str
            The temporary path where the files will be extracted and then uploaded.
        params : Dict[str, Any]
            Dict with the dataloader parameters. The options are:
            - data_key (str): The key of the json where the data is contained.

        Returns
        -------
        DatasetDict
            A HuggingFace's Dataset with the loaded data.
        """
        self._check_params(params)
        field = params["data_key"]

        if isinstance(file, str):
            dataset = load_dataset("json", data_files=file, field=field)

        elif isinstance(file, UploadFile):
            files_path = self.extract_files(temp_path, file)
            if files_path.split("/")[-1] == "files":
                try:
                    dataset = load_dataset("json", data_dir=files_path, field=field)
                finally:
                    shutil.rmtree(temp_path, ignore_errors=True)
            else:
                try:
                    dataset = load_dataset("json", data_files=files_path, field=field)
                finally:
                    os.remove(files_path)

        return dataset
