from abc import abstractmethod
from typing import Any

from DashAI.back.models.supervised_model import SupervisedModel


class TextClassificationModel(SupervisedModel):
    """Base class for models that perform text classification tasks.

    Concrete text classification models must extend this class and implement
    ``save``, ``load``, and ``train``. Compatible with ``TextClassificationTask``.
    """

    COMPATIBLE_COMPONENTS = ["TextClassificationTask"]

    @abstractmethod
    def save(self, filename: str) -> None:
        """Store the model to disk.

        Parameters
        ----------
        filename : str
            Path where the model will be saved.
        """
        raise NotImplementedError

    @abstractmethod
    def load(self, filename: str) -> Any:
        """Restore a model instance from disk.

        Parameters
        ----------
        filename : str
            Path where the model was previously saved.

        Returns
        -------
        Any
            The restored model instance.
        """
        raise NotImplementedError
