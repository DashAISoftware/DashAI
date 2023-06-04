from abc import ABCMeta, abstractmethod

from DashAI.back.config_object import ConfigObject


class BaseModel(ConfigObject, metaclass=ABCMeta):
    """
    Abstract class of all machine learning models.

    All models must extend this class and implement save and load methods.
    """

    MODEL: str
    SCHEMA: dict

    @property
    def _compatible_tasks(self) -> list:
        raise NotImplementedError

    # TODO implement a check_params method to check the params
    #  using the JSON schema file.
    # TODO implement a method to check the initialization of TASK
    #  an task params variables.

    @abstractmethod
    def save(self, filename=None):
        """Store an instance of a model.

        filename (Str): Indicates where to store the model,
        if filename is None, this method returns a bytes array with the model.
        """
        raise NotImplementedError

    @abstractmethod
    def load(self, filename):
        """Restores an instance of a model.

        filename (Str): Indicates where the model was stored.
        """
        raise NotImplementedError
