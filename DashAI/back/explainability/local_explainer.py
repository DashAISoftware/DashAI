from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset


class LocalExplainer:
    def __init__(self) -> None:
        pass

    def fit(self, X: DashAIDataset):
        return self

    def explain_instance(self, X: DashAIDataset):
        pass
