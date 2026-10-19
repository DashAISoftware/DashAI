"""Base Metric abstract class."""

from typing import Any, Dict, Final


class BaseMetric:
    """Abstract base class for all DashAI evaluation metrics.

    Every concrete metric must subclass ``BaseMetric`` (or one of its
    category subclasses) and implement a static ``score`` method. The concrete
    method signature depends on the evaluation family: supervised metrics use
    true outputs and predictions, while clustering metrics use feature data and
    discovered labels.

    Class attributes
    ----------------
    TYPE : str
        Always ``"Metric"``; used by the DashAI component registry.
    MAXIMIZE : bool
        ``True`` if higher values are better (e.g. accuracy, R²),
        ``False`` if lower values are better (e.g. MAE, RMSE).
    metadata : dict
        Optional extra metadata surfaced to the frontend via
        :meth:`get_metadata`.
    """

    TYPE: Final[str] = "Metric"
    MAXIMIZE: Final[bool] = False
    metadata: Dict[str, Any] = {}

    @classmethod
    def get_metadata(cls: "BaseMetric") -> Dict[str, Any]:
        """
        Get metadata values for the current metric.

        Returns
        -------
        Dict[str, Any]
            Dictionary with the metadata
        """
        meta: Dict[str, Any] = dict(getattr(cls, "metadata", {}) or {})
        meta["maximize"] = cls.MAXIMIZE

        return meta
