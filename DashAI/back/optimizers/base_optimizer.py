"""Base Optimizer abstract class."""

from abc import ABCMeta, abstractmethod
from typing import Final

from DashAI.back.config_object import ConfigObject


class BaseOptimizer(ConfigObject, metaclass=ABCMeta):
    """
    Abstract class of all hyperparameter's Optimizers.

    All models must extend this class and implement optimize method.
    """

    TYPE: Final[str] = "Optimizer"

    @abstractmethod
    def optimize(self, model, dataset, parameters, metric):
        """
        Optimization process

        Args:
            model (class): class for the model from the current experiment
            dataset (dict): dict with the data to train and validation
            parameters (dict): dict with the information to create the search space
            metric (class): class for the metric to optimize

        Returns
        -------
            best_model: Object from the class model with the best hyperparameters found.
        """
        raise NotImplementedError(
            "Optimization modules must implement optimize method."
        )
