from datasets import ClassLabel, Value

from DashAI.back.tasks.base_task import BaseTask


class TabularClassificationTask(BaseTask):
    """
    Class to represent the Tabular Classification task.
    Here you can change the methods provided by class Task.
    """

    name: str = "TabularClassificationTask"
    schema: dict = {
        "inputs_types": [ClassLabel, Value],
        "outputs_types": [ClassLabel, Value],
        "inputs_cardinality": "n",
        "outputs_cardinality": 1,
    }

    @staticmethod
    def create():
        return TabularClassificationTask()
