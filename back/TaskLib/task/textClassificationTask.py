import numpy as np
from TaskLib.task.taskMain import Task

class TextClassificationTask(Task):
    """
    Class to represent the Text Classifitacion task.
    Here you can change the methods provided by class Task.
    """

    NAME: str = "TextClassificationTask"

    @staticmethod
    def create():
        task = TextClassificationTask()
        return task

    def parse_input(input_data):
        # TODO reshape only if input is 1D
        x_train = np.array(input_data["train"]["x"])
        y_train = np.array(input_data["train"]["y"])
        x_test = np.array(input_data["test"]["x"])
        y_test = np.array(input_data["test"]["y"])

        return x_train, y_train, x_test, y_test
    
    def parse_single_input_from_string(self, x : str):
        return [x]