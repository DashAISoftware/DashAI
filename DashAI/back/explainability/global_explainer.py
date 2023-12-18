from abc import abstractmethod

from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset
from DashAI.back.explainability.base_explainer import BaseExplainer
from DashAI.back.models.base_model import BaseModel


class BaseGlobalExplainer(BaseExplainer):
    @abstractmethod
    def explain(self, model: BaseModel, x: DashAIDataset):
        pass
