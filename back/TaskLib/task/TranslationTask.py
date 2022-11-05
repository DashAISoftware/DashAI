from TaskLib.task.taskMain import Task
from datasets.dataset_dict import DatasetDict
from datasets import Dataset


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

    def parse_input(input_data):
        d = {'train': Dataset.from_dict(
            {'source_text': input_data["train"]["x"], 'target_text': input_data["train"]["y"]}),
             'test': Dataset.from_dict({'source_text': input_data["test"]["x"],
                                        'target_text': input_data["test"]["y"]})
             }

        d = DatasetDict(d)
        return d
