import json
import os
import pickle
from abc import ABC, abstractmethod
from typing import Any, Dict, Final

from DashAI.back.config_object import ConfigObject
from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset
from DashAI.back.models.base_model import BaseModel


class BaseLocalExplainer(ConfigObject, ABC):
    TYPE: Final[str] = "LocalExplainer"

    def save_explanation(self, filename: str) -> None:
        with open(filename, "wb") as f:
            pickle.dump(self, f, protocol=pickle.HIGHEST_PROTOCOL)

    def load_explanation(self, filename: str) -> None:
        with open(filename, "rb") as f:
            return pickle.load(f)

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        dir_path = os.path.dirname(os.path.realpath(__file__))
        with open(
            f"{dir_path}/explainers_schemas/{cls.__name__}.json",
            encoding="utf-8",
        ) as f:
            return json.load(f)

    def format_tabular_data(self, dataset: DashAIDataset):
        data_df = dataset.to_pandas()
        x = data_df.loc[:, dataset.inputs_columns]
        y = data_df[dataset.outputs_columns]

        return x, y

    @abstractmethod
    def fit(self, model: BaseModel, data: DashAIDataset):
        return self

    @abstractmethod
    def explain_instance(self, model: BaseModel, instance: DashAIDataset):
        pass
