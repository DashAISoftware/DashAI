from DashAI.back.models import BaseModel
from DashAI.back.registries.base_registry import BaseRegistry
from DashAI.back.registries.register_mixins import TaskComponentMappingMixin

<<<<<<< HEAD
#@singleton
class ModelRegistry:

    def __init__(
        self,
        task_registry: TaskRegistry,
        models: Union[List[Type[BaseModel]], None],
    ) -> None:

        self._models: dict[str, Type[BaseModel]] = {}

        if task_registry is not None:
            self._task_registry = task_registry
=======

class ModelRegistry(BaseRegistry, TaskComponentMappingMixin):
    """Centralized registry for models."""
>>>>>>> staging

    registry_for = BaseModel
