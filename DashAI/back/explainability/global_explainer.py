from abc import abstractmethod

from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset
from DashAI.back.explainability.base_explainer import BaseExplainer


class GlobalExplainer(BaseExplainer):
    def __init__(self) -> None:
        pass

    def fit(self, x: DashAIDataset):
        return self

    @abstractmethod
    def explain(self, model, x: DashAIDataset):
        pass
