from datasets import ClassLabel, DatasetDict, Value

from DashAI.back.tasks.base_task import BaseTask


class TabularClassificationTask(BaseTask):
    """
    Class to represent the Tabular Classification task.
    Here you can change the methods provided by class Task.
    """

    name: str = "TabularClassificationTask"
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
        outputs_columns = datasetdict["train"].outputs_columns
        tipos = {outputs_columns[0]: "Categorico"}
        for split in datasetdict:
            datasetdict[split] = datasetdict[split].change_columns_type(tipos)
        return datasetdict
