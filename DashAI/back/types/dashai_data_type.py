from abc import ABC, abstractmethod
from typing import Union

from datasets import ClassLabel, Image, Value

feature_type = Union[Value, Image, ClassLabel]


class DashAIDataType(ABC):
    @abstractmethod
    @staticmethod
    def from_hf_feature(hf_feature: feature_type):
        raise NotImplementedError
