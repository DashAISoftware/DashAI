import json
import logging
from abc import ABCMeta
from typing import Final

from DashAI.back.config_object import ConfigObject

logger = logging.getLogger(__name__)


class BaseMetric(ConfigObject, metaclass=ABCMeta):
    """
    Abstract class of all metrics
    """

    TYPE: Final[str] = "Metric"

    @property
    def _compatible_tasks(self) -> list:
        raise NotImplementedError

    @classmethod
    def get_schema(cls) -> dict:
        """
        This method load the schema JSON file asocciated to the metric.
        """
        try:
            with open(
                f"DashAI/back/metrics/metrics_schemas/{cls.__name__}.json", "r"
            ) as f:
                schema = json.load(f)
            return schema
        except FileNotFoundError:
            logger.exception(
                (
                    f"Could not load the schema for {cls.__name__} : File DashAI/back"
                    f"/metrics/metrics_schemas/{cls.__name__}.json not found."
                )
            )
            return {}
