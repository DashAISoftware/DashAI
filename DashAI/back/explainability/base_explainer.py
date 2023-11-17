from abc import ABC, abstractmethod


class BaseExplainer(ABC):
    def __init__(self) -> None:
        pass

    @abstractmethod
    def load(self):
        pass

    @abstractmethod
    def save(self):
        pass
