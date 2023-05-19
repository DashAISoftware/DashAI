import os

from datasets import DatasetDict, load_dataset
from starlette.datastructures import UploadFile

from DashAI.back.dataloaders.classes.tabular_dataloader import TabularDataLoader


class CSVDataLoader(TabularDataLoader):
    """
    Data loader for tabular data in CSV files
    """

    def load_data(
        self,
        dataset_path: str,
        params: dict[str, any],
        file: UploadFile = None,
        url: str = None,
    ) -> DatasetDict:
        """
        Load the dataset uploaded in CSV files in a DatasetDict

        Args:
            dataset_path (str): Path of the folder with the dataset files.
            params (dict[str, any]): Dict with the parameters for loading CSV files.
                These parameters are:
                    - separator (str): The character that delimits the CSV data.

            file (UploadFile, optional): File uploaded.
                It's optional because is not necessary if dataset is uploaded in a URL.

            url (str, optional): For load the dataset from an URL.
                It's optional because is not necessary if dataset is uploaded in files.

        Returns:
            DatasetDict: Dataset loaded in Hugging Face format.
        """
        if file is None and url is None:
            raise ValueError("Dataset should be a file or a url, both are None")
        if file is not None and url is not None:
            raise ValueError("Dataset should be a file or a url, got both")
        if not isinstance(dataset_path, str):
            raise TypeError(
                f"dataset_path should be a string, got {type(dataset_path)}"
            )
        if not isinstance(params, dict):
            raise TypeError(f"params should be a dict, got {type(params)}")

        if "separator" not in params.keys():
            raise ValueError("separator parameter is needed for load CSV files.")
        else:
            if not isinstance(params["separator"], str):
                raise TypeError(
                    "params['separator'] should be a string, "
                    + f"got {type(params['separator'])}"
                )
        if not isinstance(file, (UploadFile, type(None))):
            raise TypeError(
                f"file should be an uploaded file from user, got {type(file)}",
            )
        if not isinstance(url, (str, type(None))):
            raise TypeError(
                f"url should be a string with a web site adress, got {type(url)}",
            )

        separator = params["separator"]
        if url:
            dataset = load_dataset("csv", data_files=url, sep=separator)
        elif file:
            files_path = self.extract_files(dataset_path, file)
            if files_path.split("/")[-1] == "files":
                dataset = load_dataset("csv", data_dir=files_path, sep=separator)
            else:
                dataset = load_dataset("csv", data_files=files_path, sep=separator)
            os.remove(files_path)  # remove the original files to not duplicate the data
        return dataset
