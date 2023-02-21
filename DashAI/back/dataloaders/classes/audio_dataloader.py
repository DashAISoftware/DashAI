import io
import zipfile

from DashAI.back.dataloaders.classes.dataloader import DataLoader
from datasets import Audio, load_dataset


class AudioDataLoader(DataLoader):
    """
    Data loader for data from audio files
    """

    def load_data(self, dataset_path, params, file=None, url=None):
        if url:
            dataset = load_dataset("audiofolder", data_files=url).cast_column(
                "audio", Audio(decode=False)
            )
        elif file:
            if file.content_type == "application/zip":
                with zipfile.ZipFile(io.BytesIO(file.file.read()), "r") as zip_file:
                    zip_file.extractall(path=f"{dataset_path}/files")
                dataset = load_dataset(
                    "audiofolder", data_dir=dataset_path + "/files"
                ).cast_column("audio", Audio(decode=False))
            else:
                raise Exception("For audio data is necessary a zip file.")
        return dataset

    def set_task_format(self, task):
        pass  # call to format method in task class
