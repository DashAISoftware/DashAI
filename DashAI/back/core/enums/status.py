from enum import Enum


class RunStatus(Enum):
    NOT_STARTED = 0
    DELIVERED = 1
    STARTED = 2
    FINISHED = 3
    ERROR = 4
