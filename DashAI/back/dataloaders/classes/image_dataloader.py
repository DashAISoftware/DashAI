from datasets import DatasetDict, load_dataset
from starlette.datastructures import UploadFile

from DashAI.back.dataloaders.classes.dataloader import BaseDataLoader


class ImageDataLoader(BaseDataLoader):
    """Data loader for data from image files."""

    COMPATIBLE_COMPONENTS = ["ImageClassificationTask"]

    def load_data(
        self,
        dataset_path: str,
        file: UploadFile = None,
        url: str = None,
    ) -> DatasetDict:
        """
        Load image data uploaded in a zip file in a DatasetDict.

        Args:
            dataset_path (str): Path of the folder with the dataset files.
            file (UploadFile, optional): File uploaded.
                It's optional because is not necessary if dataset is uploaded in a URL.

            url (str, optional): For load the dataset from an URL.
                It's optional because is not necessary if dataset is uploaded in files.

        Returns
        -------
            DatasetDict: Dataset loaded in Hugging Face format.
        -------------------------------------------------------------------------------
        - NOTE: For image data, the original files are saved in "/files" folder and
                the DatasetDict should have only the path to the images in "/files"
                If decode is True, data is duplicated in DatasetDict as a PIL object.

                More information: https://huggingface.co/docs/datasets/image_load
        -------------------------------------------------------------------------------
        """
        if file is None and url is None:
            raise ValueError("Dataset should be a file or a url, both are None")
        if file is not None and url is not None:
            raise ValueError("Dataset should be a file or a url, got both")
        if not isinstance(dataset_path, (str, type(None))):
            raise TypeError(
                f"dataset_path should be a string, got {type(dataset_path)}"
            )
        if not isinstance(file, (UploadFile, type(None))):
            raise TypeError(
                f"file should be an uploaded file from user, got {type(file)}"
            )
        if not isinstance(url, (str, type(None))):
            raise TypeError(
                f"url should be a string with a web site adress, got {type(url)}"
            )

        if url:
            dataset = load_dataset("imagefolder", data_files=url)
        elif file:
            if file.content_type == "application/zip":
                files_path = self.extract_files(dataset_path, file)
                dataset = load_dataset("imagefolder", data_dir=files_path)
            else:
                raise Exception("For image data is necessary a zip file.")
        return dataset
