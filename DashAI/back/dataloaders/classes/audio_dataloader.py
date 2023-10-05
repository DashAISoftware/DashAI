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
        filepath_or_buffer: Union[UploadFile, str],
        temp_path: str,
        params: Dict[str, Any],
    ) -> DatasetDict:
        """Load and audio dataset into a DatasetDict.

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
            dataset = load_dataset(
                "audiofolder",
                data_files=filepath_or_buffer,
            ).cast_column(
                "audio",
                Audio(decode=False),
            )

        elif isinstance(filepath_or_buffer, UploadFile):
            if filepath_or_buffer.content_type == "application/zip":
                files_path = self.extract_files(temp_path, filepath_or_buffer)

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
                    "The following content type was delivered: "
                    f"{filepath_or_buffer.content_type}"
                )
        return dataset
