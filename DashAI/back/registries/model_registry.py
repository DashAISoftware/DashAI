from DashAI.back.models import BaseModel
from DashAI.back.registries.base_registry import BaseRegistry
from DashAI.back.registries.mixins import TaskComponentMappingMixin


class ModelRegistry(BaseRegistry, TaskComponentMappingMixin):
    """Centralized registry for models."""

    registry_for = BaseModel
