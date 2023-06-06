from abc import ABCMeta
from typing import Final

from DashAI.back.config_object import ConfigObject


class BaseMetric(ConfigObject, metaclass=ABCMeta):
    """
    Abstract class of all metrics
    """

    TYPE: Final[str] = "Metric"

    @property
    def _compatible_tasks(self) -> list:
        raise NotImplementedError
