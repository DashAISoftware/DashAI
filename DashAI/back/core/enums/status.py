from enum import Enum


class RunStatus(Enum):
    NOT_STARTED = 0
    STARTED = 1
    FINISHED = 2
    ERROR = 3


class UserStep(Enum):
    TASK_SELECTION = 0
    DATASET_SELECTION = 1
    MODEL_CONFIGURATION = 2
    EXECUTION = 3
    COMPLETED = 4
