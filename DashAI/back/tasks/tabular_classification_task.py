from typing import Union

import numpy as np
from datasets import Dataset
from datasets.dataset_dict import DatasetDict

from DashAI.back.tasks.task import Task


class TabularClassificationTask(Task):
    """
    Class to represent the Tabular Classification task.
    Here you can change the methods provided by class Task.
    """

    NAME: str = "TabularClassificationTask"

    @staticmethod
    def create():
        return TabularClassificationTask()

    def validate_dataset(self, dataset: DatasetDict, class_column: Union[str, int]):
        """Validate that a dataset is compatible with this task.

        Args:
            dataset (DatasetDict): Uploaded dataset in a DatasetDict.
            class_column (str/int): Name or index of class column of the dataset.

        Returns:
            str: An error message or 'None' if validation is succesfull.
        -------------------------------------------------------------------------
        - NOTE: When find an error in the dataset format, it return an string
                and not raises an error, because on front end we need receive
                a message in string to show the error to user.
        -------------------------------------------------------------------------
        """
        if not isinstance(dataset, DatasetDict):
            raise TypeError(f"dataset should be a DatasetDict, got {type(dataset)}")
        if not (isinstance(class_column, str) or isinstance(class_column, int)):
            raise TypeError(
                f"class_column should be a integer or string, got {type(class_column)}"
            )

        columns = dataset["train"].column_names
        if dataset.num_rows["train"] < 10:
            return (
                "Not enought samples. Make sure that you have "
                + "enought samples for split your data."
            )
        if dataset.num_columns["train"] < 2:
            return (
                "Not enough features. Make sure you have at least one feature that"
                + " classifies the data and one on which to perform classification."
            )

        # Check if class column exist
        if isinstance(class_column, int):
            if class_column < len(columns):
                class_column = columns[class_column]
            else:
                return f"Class column index {class_column} does not exist in dataset."
        else:
            if class_column not in columns:
                return f"Class column '{class_column}' does not exist in dataset."

        # Check data types of each feature
        for col in columns:
            data_type = dataset["train"].features[col].dtype
            if col == class_column:
                pass  # TODO: Check for type of data for class column
            elif ("float" not in data_type) and ("int" not in data_type):
                return (
                    "Dataset have non-numerical data. "
                    + f"Make sure you have only numeric data for {self.NAME}."
                )
        return None

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
