from datasets import Dataset
from datasets.dataset_dict import DatasetDict
from TaskLib.task.taskMain import Task


class TranslationTask(Task):
    """
    Abstract class for translation tasks.
    Here you can change the methods provided by class TranslationTask.
    """

    NAME: str = "TranslationTask"
    SOURCE: str = ""
    TARGET: str = ""

    @staticmethod
    def create():
        task = TranslationTask()
        return task

    def parse_input(self, input_data):
        d = {
            "train": Dataset.from_dict(
                {"x": input_data["train"]["x"], "y": input_data["train"]["y"]}
            ),
            "test": Dataset.from_dict(
                {"x": input_data["test"]["x"], "y": input_data["test"]["y"]}
            ),
        }

        d = DatasetDict(d)
        return d
