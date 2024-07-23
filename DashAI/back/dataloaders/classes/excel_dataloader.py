"""DashAI Excel Dataloader."""

import os
from typing import Any, Dict, Union

import pandas as pd
from beartype import beartype
from datasets import Dataset, DatasetDict
from starlette.datastructures import UploadFile

from DashAI.back.core.schema_fields import (
    int_field,
    none_type,
    schema_field,
    string_field,
    union_type,
)
from DashAI.back.core.schema_fields.base_schema import BaseSchema
from DashAI.back.dataloaders.classes.dataloader import (
    BaseDataLoader,
    DataloaderMoreOptionsSchema,
    DatasetSplitsSchema,
)


class ExcelDataloaderSchema(BaseSchema):
    name: schema_field(
        none_type(string_field()),
        "",
        (
            "Custom name to register your dataset. If no name is specified, "
            "the name of the uploaded file will be used."
        ),
    )  # type: ignore
    sheet: schema_field(
        union_type(int_field(ge=0), string_field()),
        placeholder=0,
        description="""
        The name of the sheet to read or its zero-based index.
        If a string is provided, the reader will search for a sheet named exactly as
        the string.
        If an integer is provided, the reader will select the sheet at the corresponding
        index.
        By default, the first sheet will be read.
        """,
    )  # type: ignore
    header: schema_field(
        none_type(int_field(ge=0)),
        placeholder=0,
        description="""
        The row number where the column names are located, indexed from 0.
        If null, the file will be considered to have no columns.
        """,
    )  # type: ignore
    usecols: schema_field(
        none_type(string_field()),
        placeholder=None,
        description="""
        If None, the reader will load all columns.
        If str, then indicates comma separated list of Excel column letters and column
        ranges (e.g. “A:E” or “A,C,E:F”). Ranges are inclusive of both sides.
        """,
    )  # type: ignore
    splits: DatasetSplitsSchema
    more_options: DataloaderMoreOptionsSchema


class ExcelDataLoader(BaseDataLoader):
    """Data loader for tabular data in Excel files."""

    COMPATIBLE_COMPONENTS = ["TabularClassificationTask"]
    SCHEMA = ExcelDataloaderSchema

    @beartype
    def load_data(
        self,
        filepath_or_buffer: Union[UploadFile, str],
        temp_path: str,
        params: Dict[str, Any],
    ) -> DatasetDict:
        """Load the uploaded Excel files into a DatasetDict.

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

        if isinstance(filepath_or_buffer, str):
            dataset = dataset = pd.read_excel(
                io=filepath_or_buffer,
                sheet_name=params["sheet"],
                header=params["header"],
                usecols=params["usecols"],
            )

        elif isinstance(filepath_or_buffer, UploadFile):
            file_path = self.extract_files(
                temp_path,
                filepath_or_buffer,
            )
            if file_path.split("/")[-1] == "files":
                raise ValueError("ExcelReader supports only one file.")
            else:
                try:
                    dataset = pd.read_excel(
                        io=file_path,
                        sheet_name=params["sheet"],
                        header=params["header"],
                        usecols=params["usecols"],
                    )
                finally:
                    os.remove(file_path)

        else:
            raise RuntimeError("filepath_or_buffer type error.")

        return DatasetDict({"train": Dataset.from_pandas(dataset)})
