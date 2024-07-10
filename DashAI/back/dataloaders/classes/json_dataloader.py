"""DashAI JSON Dataloader."""

import os
import shutil
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


class JSONDataloaderSchema(BaseSchema):
    name: schema_field(
        none_type(string_field()),
        "",
        (
            "Custom name to register your dataset. If no name is specified, "
            "the name of the uploaded file will be used."
        ),
    )  # type: ignore
    data_key: schema_field(
        string_field(),
        "data",
        "Name of key that contains the data in the JSON files.",
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


class JSONDataLoader(BaseDataLoader):
    """Data loader for tabular data in JSON files."""

    COMPATIBLE_COMPONENTS = [
        "TabularClassificationTask",
        "TextClassificationTask",
        "TranslationTask",
    ]
    SCHEMA = JSONDataloaderSchema

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
        filepath_or_buffer: Union[UploadFile, str],
        temp_path: str,
        params: Dict[str, Any],
    ) -> DatasetDict:
        """Load the uploaded JSON dataset into a DatasetDict.

        Parameters
        ----------
        filepath_or_buffer : Union[UploadFile, str], optional
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

        if isinstance(filepath_or_buffer, str):
            dataset = load_dataset("json", data_files=filepath_or_buffer, field=field)

        elif isinstance(filepath_or_buffer, UploadFile):
            files_path = self.extract_files(temp_path, filepath_or_buffer)
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
