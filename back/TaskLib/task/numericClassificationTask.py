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