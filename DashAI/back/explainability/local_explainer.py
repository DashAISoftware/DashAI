import json
import os
from abc import ABC, abstractmethod
from typing import Any, Dict, Final

from sklearn.preprocessing import OneHotEncoder

from DashAI.back.config_object import ConfigObject
from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset
from DashAI.back.models.base_model import BaseModel


class BaseLocalExplainer(ConfigObject, ABC):
    """Base class for local explainers."""

    TYPE: Final[str] = "LocalExplainer"

    def __init__(self, model: BaseModel) -> None:
        self.model = model
        self.explanation = None

    def save_explanation(self, path: str) -> None:
        with open(path, "w") as f:
            json.dump(self.explanation, f)

    @staticmethod
    def load_explanation(self, path: str) -> None:
        with open(path, "r") as f:
            return json.load(f)

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        dir_path = os.path.dirname(os.path.realpath(__file__))
        with open(
            f"{dir_path}/explainers_schemas/{cls.__name__}.json",
            encoding="utf-8",
        ) as f:
            return json.load(f)

    def format_tabular_data(
        self, dataset: DashAIDataset, one_hot_encoding: bool = "False"
    ):
        data_df = dataset.to_pandas()
        x = data_df.loc[:, dataset.inputs_columns]
        y = data_df[dataset.outputs_columns]

        if one_hot_encoding:
            encoder = OneHotEncoder().fit(y)
            y = encoder.transform(y).toarray()

        return x, y

    @abstractmethod
    def fit(self, data: DashAIDataset, *args, **kwargs):
        return self

    # TODO: implement is_fitted?
    @abstractmethod
    def explain_instance(self, instance: DashAIDataset):
        raise NotImplementedError
