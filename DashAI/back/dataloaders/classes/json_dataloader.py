import os
from typing import Dict

from datasets import DatasetDict, load_dataset
from fastapi import UploadFile

from DashAI.back.dataloaders.classes.tabular_dataloader import TabularDataLoader


class JSONDataLoader(TabularDataLoader):
    """
    Data loader for tabular data in JSON files
    """

    def load_data(
        self,
        dataset_path: str,
        params: Dict[str, any],
        file: UploadFile = None,
        url: str = None,
    ) -> DatasetDict:
        """
        Load the dataset uploaded in JSON files in a DatasetDict

        Args:
            dataset_path (str): Path of the folder with the dataset files.
            params (dict[str, any]): Dict with the parameters for loading JSON files.
                These parameters are:
                    - data_key (str): The key of the json where the data is contained.

            file (UploadFile, optional): File uploaded.
                It's optional because is not necessary if dataset is uploaded in a URL.

            url (str, optional): For load the dataset from an URL.
                It's optional because is not necessary if dataset is uploaded in files.

        Returns:
            DatasetDict: Dataset loaded in Hugging Face format.
        """
        if not isinstance(dataset_path, str):
            raise TypeError(
                f"dataset_path should be a string, got {type(dataset_path)}"
            )
        if not isinstance(params, dict):
            raise TypeError(f"params should be a dict, got {type(params)}")

        if "data_key" not in params.keys():
            raise ValueError("data_key parameter is needed for load JSON files.")
        else:
            if not isinstance(params["data_key"], str):
                raise TypeError(
                    "params['data_key'] should be a string, "
                    + f"got {type(params['data_key'])}"
                )
        if not isinstance(file, UploadFile):
            raise TypeError(
                f"file should be an uploaded file from user, got {type(file)}"
            )
        if not isinstance(url, str):
            raise TypeError(
                f"url should be a string with a web site adress, got {type(url)}"
            )

        field = params["data_key"]
        if url:
            dataset = load_dataset("json", data_files=url, field=field)
        elif file:
            files_path = self.extract_files(dataset_path, file)
            if files_path.split("/")[-1] == "files":
                dataset = load_dataset("json", data_dir=files_path, field=field)
            else:
                dataset = load_dataset("json", data_files=files_path, field=field)
            os.remove(files_path)  # remove the original files to not duplicate the data
        return dataset
