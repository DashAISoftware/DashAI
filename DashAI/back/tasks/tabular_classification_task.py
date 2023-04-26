from typing import Union, List

import numpy as np
from datasets import Dataset
from datasets import Value
from datasets import ClassLabel
from datasets.dataset_dict import DatasetDict

from DashAI.back.tasks.base_task import BaseTask

class TabularClassificationTask(BaseTask):
    """
    Class to represent the Tabular Classification task.
    Here you can change the methods provided by class Task.
    """

    name: str = "TabularClassificationTask"
    schema: dict = {"inputs_types": [ClassLabel, Value], "outputs_types": [ClassLabel, Value],
                    "inputs_cardinality": "n", "outputs_cardinality": 1}


    @staticmethod
    def create():
        return TabularClassificationTask()

