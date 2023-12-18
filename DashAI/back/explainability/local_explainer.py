from abc import abstractmethod

from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset
from DashAI.back.models.base_model import BaseModel


class BaseLocalExplainer:
    def fit(self, model: BaseModel, data: DashAIDataset):
        return self

    @abstractmethod
    def explain_instance(self, model: BaseModel, instance: DashAIDataset):
        pass
