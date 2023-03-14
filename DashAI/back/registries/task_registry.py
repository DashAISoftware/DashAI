"""Task Registry implementation."""

from DashAI.back.registries.base_registry import BaseRegistry
from DashAI.back.tasks.base_task import BaseTask


class TaskRegistry(BaseRegistry):
    """Centralized registry for tasks."""

    registry_for = BaseTask
