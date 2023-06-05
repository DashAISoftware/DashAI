from datasets import Dataset
from datasets.dataset_dict import DatasetDict

from DashAI.back.tasks.base_task import BaseTask


class TranslationTask(BaseTask):
    """Base class for translation tasks."""

    source: str = ""
    target: str = ""

    def parse_input(self, input_data):
        d = {
            "train": Dataset.from_dict(
                {"x": input_data["train"]["x"], "y": input_data["train"]["y"]},
            ),
            "test": Dataset.from_dict(
                {"x": input_data["test"]["x"], "y": input_data["test"]["y"]},
            ),
        }

        d = DatasetDict(d)
        return d
