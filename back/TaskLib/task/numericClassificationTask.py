from TaskLib.task.taskMain import Task


class NumericClassificationTask(Task):
    """
    Abstarct class for text classification tasks.
    Never use this class directly.
    """

    NAME: str = "NumericClassificationTask"

    @staticmethod
    def create():
        return NumericClassificationTask()
    
    def parse_single_input_from_string(self, x_string : str):
        splited_x = x_string.split(",")
        output = []
        for x in splited_x:
            output.append(int(x))
        return [output]