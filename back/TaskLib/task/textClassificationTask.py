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
        return TextClassificationTask()
    
    def parse_single_input_from_string(self, x : str):
        return [x]