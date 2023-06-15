from datasets import DatasetDict, Sequence, Value

from DashAI.back.tasks.base_task import BaseTask


class TranslationTask(BaseTask):
    """Base class for translation task.
    Here you can change the methods provided by class Task.
    """

    schema: dict = {
        "inputs_types": [Value, Sequence],
        "outputs_types": [Value, Sequence],
        "inputs_cardinality": 1,
        "outputs_cardinality": 1,
    }

    @staticmethod
    def create():
        return TranslationTask()

    def prepare_for_task(self, datasetdict: DatasetDict):
        """Change the column types to suit the tabular classification task.

        A copy of the dataset is created.

        Parameters
        ----------
        datasetdict : DatasetDict
            Dataset to be changed

        Returns
        -------
        DatasetDict
            Dataset with the new types
        """
        pass
        return datasetdict
