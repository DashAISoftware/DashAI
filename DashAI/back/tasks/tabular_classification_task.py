from datasets import ClassLabel, DatasetDict, Value

from DashAI.back.tasks.base_task import BaseTask


class TabularClassificationTask(BaseTask):
    """Base class for tabular classification tasks.

    Here you can change the methods provided by class Task.
    """

    DESCRIPTION: str = "Classify data with Tabular features by categories."
    schema: dict = {
        "inputs_types": [ClassLabel, Value],
        "outputs_types": [ClassLabel],
        "inputs_cardinality": "n",
        "outputs_cardinality": 1,
    }

    @staticmethod
    def create():
        return TabularClassificationTask()

    def prepare_for_task(self, datasetdict: DatasetDict):
        """Change the column types to suit the tabular classification task.

        A copy of the dataset is created.

        Parameters
        ----------
        dataset : DatasetDict
            Dataset to be changed

        Returns
        -------
        DatasetDict
            Dataset with the new types
        """
        outputs_columns = datasetdict["train"].outputs_columns
        types = {outputs_columns[0]: "Categorical"}
        for split in datasetdict:
            datasetdict[split] = datasetdict[split].change_columns_type(types)
        return datasetdict
