from abc import ABCMeta, abstractmethod
from configObject import ConfigObject


# version == 1.0.0
class Model(ConfigObject):
    """
    Abstract class of all machine learning models.
    The models must implement the save and load methods.
    """

    MODEL: str
    SCHEMA: dict

    # TODO implement a check_params method to check the params
    #  using the JSON schema file.
    # TODO implement a method to check the initialization of TASK
    #  an task params variables.

    @abstractmethod
    def save(self, filename=None):
        """
        Stores an instance of a model.

        filename (Str): Indicates where to store the model,
        if filename is None, this method returns a bytes array with the model.
        """
        pass

    @staticmethod
    def load(filename):
        """
        Restores an instance of a model

        filename (Str): Indicates where the model was stored.
        """
        pass