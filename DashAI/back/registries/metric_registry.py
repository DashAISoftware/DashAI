"""Metric Registry implementation."""

from DashAI.back.metrics.base_metric import BaseMetric
from DashAI.back.registries.base_registry import BaseRegistry
from DashAI.back.registries.register_mixins import TaskComponentMappingMixin


class MetricRegistry(BaseRegistry, TaskComponentMappingMixin):
    """Centralized registry for metrics."""

    registry_for = BaseMetric
