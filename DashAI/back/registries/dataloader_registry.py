from DashAI.back.dataloaders import BaseDataLoader
from DashAI.back.registries.base_registry import BaseRegistry
from DashAI.back.registries.register_mixins import TaskComponentMappingMixin


class DataloaderRegistry(BaseRegistry, TaskComponentMappingMixin):
    """Centralized registry for models."""

    registry_for = BaseDataLoader
