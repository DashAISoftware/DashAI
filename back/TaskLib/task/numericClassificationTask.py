from TaskLib.task.taskMain import Task


class NumericClassificationTask(Task):
    """
    Class to represent the Numerical Classifitacion task.
    Here you can change the methods provided by class Task.
    """

    NAME: str = "NumericClassificationTask"

    @staticmethod
    def create():
        return NumericClassificationTask()
    
    def parse_single_input_from_string(self, x_string : str):
        splited_x = x_string.split(",")
        output = []
        for x in splited_x:
            output.append(float(x))
        return [output]