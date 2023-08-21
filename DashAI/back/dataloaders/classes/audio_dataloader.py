"""DashAI Audio Dataloader."""
from typing import Any, Dict, Union

from beartype import beartype
from datasets import Audio, DatasetDict, load_dataset
from starlette.datastructures import UploadFile

from DashAI.back.dataloaders.classes.dataloader import BaseDataLoader


class AudioDataLoader(BaseDataLoader):
    """Data loader for data from audio files."""

    @beartype
    def load_data(
        self,
        file: Union[UploadFile, str],
        temp_path: str,
        params: Dict[str, Any],
    ) -> DatasetDict:
        """Load and audio dataset into a DatasetDict.

        Parameters
        ----------
        file : Union[UploadFile, str], optional
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
        if isinstance(file, str):
            dataset = load_dataset(
                "audiofolder",
                data_files=file,
            ).cast_column(
                "audio",
                Audio(decode=False),
            )

        elif isinstance(file, UploadFile):
            if file.content_type == "application/zip":
                files_path = self.extract_files(temp_path, file)

                dataset = load_dataset(
                    "audiofolder",
                    data_dir=files_path,
                ).cast_column(
                    "audio",
                    Audio(decode=False),
                )
            else:
                raise Exception(
                    "The audio dataloader requires the input file to be a zip file. "
                    f"The following content type was delivered: {file.content_type}"
                )
        return dataset
