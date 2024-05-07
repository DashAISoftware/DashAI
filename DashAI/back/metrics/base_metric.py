"""Base Metric abstract class."""

from typing import Final


class BaseMetric:
    """Abstract class of all metrics."""

    TYPE: Final[str] = "Metric"
