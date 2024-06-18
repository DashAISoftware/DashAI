from enum import Enum


class ExplainerStatus(Enum):
    NOT_STARTED = 0
    DELIVERED = 1
    STARTED = 2
    FINISHED = 3
    ERROR = 4


class RunStatus(Enum):
    NOT_STARTED = 0
    DELIVERED = 1
    STARTED = 2
    FINISHED = 3
    ERROR = 4


class PluginStatus(Enum):
    REGISTERED = 1
    INSTALLED = 2
    ERROR = 99
