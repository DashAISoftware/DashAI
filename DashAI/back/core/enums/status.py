from enum import Enum


class RunStatus(Enum):
    NOT_STARTED = 0
    DELIVERED = 1
    STARTED = 2
    FINISHED = 3
    ERROR = 4


class UserStep(Enum):
    TASK_SELECTION = 0
    DATASET_SELECTION = 1
    MODEL_CONFIGURATION = 2
    EXECUTION = 3
    COMPLETED = 4
