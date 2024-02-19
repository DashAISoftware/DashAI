from enum import Enum


class ExplainerStatus(Enum):
    DELIVERED = 0
    STARTED = 1
    FINISHED = 2
    ERROR = 3


class RunStatus(Enum):
    NOT_STARTED = 0
    DELIVERED = 1
    STARTED = 2
    FINISHED = 3
    ERROR = 4
