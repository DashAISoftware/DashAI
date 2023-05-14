from abc import ABCMeta

from DashAI.back.config_object import ConfigObject


class BaseMetric(ConfigObject, metaclass=ABCMeta):
    """
    Abstract class of all machine learning models. #todo
    """

    @property
    def _compatible_tasks(self) -> list:
        raise NotImplementedError
