import numpy as np
from datasets import Dataset
from datasets.dataset_dict import DatasetDict

from DashAI.back.tasks.base_task import BaseTask


class TabularClassificationTask(BaseTask):
    """
    Class to represent the Numerical Classification task.
    Here you can change the methods provided by class Task.
    """

    name: str = "TabularClassificationTask"

    @staticmethod
    def create():
        return TabularClassificationTask()

    def parse_input(self, input_data):
        # TODO reshape only if input is 1D
        x_train = np.array(input_data["train"]["x"])
        y_train = np.array(input_data["train"]["y"])
        x_test = np.array(input_data["test"]["x"])
        y_test = np.array(input_data["test"]["y"])

        self.categories = []
        for cat in y_train:
            if cat not in self.categories:
                self.categories.append(cat)
        for cat in y_test:
            if cat not in self.categories:
                self.categories.append(cat)

        numeric_y_train = []
        for sample in y_train:
            numeric_y_train.append(self.categories.index(sample))
        numeric_y_test = []
        for sample in y_test:
            numeric_y_test.append(self.categories.index(sample))

        d = {
            "train": Dataset.from_dict({"x": x_train, "y": numeric_y_train}),
            "test": Dataset.from_dict({"x": x_test, "y": numeric_y_test}),
        }
        d = DatasetDict(d)

        return d

    def map_category(self, index):
        """Returns the original category for the index artificial category"""
        return self.categories[index]

    def get_prediction(self, execution_id, x):
        """Returns the predicted output of x, given by the execution execution_id"""
        cat = self.executions[execution_id].predict(
            self.parse_single_input_from_string(x)
        )
        final_cat = self.map_category(int(cat[0]))
        return final_cat

    def parse_single_input_from_string(self, x_string: str):
        splited_x = x_string.split(",")
        output = []
        for x in splited_x:
            output.append(float(x))
        return [output]
