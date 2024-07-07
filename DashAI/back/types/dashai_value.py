from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from datasets import Value


@dataclass
class DashAIValue(ABC, Value):
    dtype: str = field(default="", init=False)

    @abstractmethod
    def __post_init__(self):
        return super().__post_init__()

    @staticmethod
    @abstractmethod
    def from_value(value: Value):
        pass
