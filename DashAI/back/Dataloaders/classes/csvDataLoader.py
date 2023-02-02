import io
import os
import zipfile

from Dataloaders.classes.dataLoaderMain import DataLoader
from datasets import load_dataset


class CSVDataLoader(DataLoader):
    """
    Data loader for tabular data in CSV files
    """

    def load_data(self, dataset_path, params, file=None, url=None):
        separator = params["separator"]
        if url:
            dataset = load_dataset("csv", data_files=url, sep=separator)
        elif file:
            if file.content_type == "application/zip":
                with zipfile.ZipFile(io.BytesIO(file.file.read()), "r") as zip_file:
                    zip_file.extractall(path=f"{dataset_path}/files")
                dataset = load_dataset(
                    "csv", data_dir=f"{dataset_path}/files", sep=separator
                )
                os.remove(f"{dataset_path}/files")
            else:
                with open(f"{dataset_path}/{file.filename}", "wb") as f:
                    f.write(file.file.read())
                dataset = load_dataset("csv", data_dir=dataset_path, sep=separator)
                os.remove(f"{dataset_path}/{file.filename}")
        return dataset

    def set_task_format(self, task):
        pass  # call to format method in task class
