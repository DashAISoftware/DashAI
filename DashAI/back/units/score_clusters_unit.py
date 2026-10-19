"""Unit that scores a fitted clustering over the features it was fitted on."""

import logging
import math
from typing import TYPE_CHECKING, Dict, List

import numpy as np

from DashAI.back.core.schema_fields import (
    BaseSchema,
    list_field,
    schema_field,
    string_field,
)
from DashAI.back.core.utils import MultilingualString
from DashAI.back.job.base_job import JobError
from DashAI.back.units.base_unit import BaseUnit
from DashAI.back.units.context import ExecutionContext

if TYPE_CHECKING:
    from DashAI.back.metrics.base_metric import BaseMetric

log = logging.getLogger(__name__)


def clustering_metrics_field():
    return schema_field(
        list_field(string_field()),
        placeholder=["Silhouette", "DaviesBouldin", "CalinskiHarabasz"],
        description=MultilingualString(
            en="Clustering metrics to score the fitted model with, by name.",
            es="Métricas de clustering con las que puntuar el modelo ajustado, "
            "por nombre.",
            pt="Métricas de clustering para pontuar o modelo ajustado, por nome.",
            de="Clustering-Metriken, mit denen das angepasste Modell bewertet "
            "wird, nach Namen.",
            zh="用于评估已拟合模型的聚类指标（按名称）。",
        ),
        alias=MultilingualString(
            en="Metrics", es="Métricas", pt="Métricas", de="Metriken", zh="指标"
        ),
    )


class ScoreClustersSchema(BaseSchema):
    metrics: clustering_metrics_field()  # type: ignore


class ScoreClustersUnit(BaseUnit):
    """Score a fitted clustering over every row of the features it was fitted on.

    Reads the cluster labels off the model, refuses a clustering that has
    nothing to measure, and scores the labels with each metric. The scores are
    published as ``{"full": {metric name: score}}`` -- the shape
    ``EvaluateModelToArtifactUnit`` gives its ``metrics`` -- and nothing is
    written: whoever ran the unit decides where they go. A job writes them as
    ``Metric`` rows; a pipeline keeps them as an artifact.

    Three failures are reported apart, each with the text it always had:

    - the labels cannot be read: "Model training failed ...", because to the
      user the labels are what training produced;
    - fewer than two clusters, or one per point: the internal validity indices
      are not defined there, so the run has no result to report;
    - a metric raises: "Metric calculation failed ...".

    A metric that answers ``None`` (undefined for these labels) or a
    non-finite number is left out of the result rather than recorded, the same
    rule ``BaseModel._score_split`` applies to supervised scores: a NaN that
    reaches a comparison poisons every one downstream of it.
    """

    SCHEMA = ScoreClustersSchema

    REQUIRES = ("model", "features")
    PROVIDES = ("metrics",)

    def __init__(self, **config) -> None:
        super().__init__(**config)
        self._metric_classes = None

    def _resolve_metrics(self) -> List["BaseMetric"]:
        """Resolve the metric classes from the registry, memoized on this unit."""
        if self._metric_classes is not None:
            return self._metric_classes

        from kink import di

        component_registry = di["component_registry"]
        resolved = []
        for name in self.config["metrics"]:
            try:
                resolved.append(component_registry[name]["class"])
            except Exception as e:
                log.exception(e)
                raise JobError(
                    f"Unable to find Metric with name {name} in registry."
                ) from e
        self._metric_classes = resolved
        return resolved

    def validate(self, ctx: ExecutionContext) -> None:
        self._resolve_metrics()

    def execute(self, ctx: ExecutionContext) -> None:
        model = ctx.require("model")
        features = ctx.require("features")
        metrics = self._resolve_metrics()

        try:
            labels = model.get_cluster_labels(features)
        except Exception as e:
            log.exception(e)
            raise JobError(f"Model training failed {e}") from e

        # Internal validity indices are only defined over two or more clusters,
        # which is why the metrics answer None outside that range. Left alone, a
        # density based model that sends every sample to noise would finish the
        # run green with an empty metric table and nothing pointing at the
        # parameters that caused it, so the degenerate outcome is raised here.
        label_values = np.asarray(labels)
        clustered = label_values[label_values != -1]
        n_noise = int(label_values.size - clustered.size)
        n_clusters = int(np.unique(clustered).size)
        if n_clusters < 2 or n_clusters >= clustered.size:
            raise JobError(
                f"{type(model).__name__} produced {n_clusters} cluster(s) over "
                f"{label_values.size} samples, {n_noise} of them labelled as "
                "noise. Clustering metrics need at least two clusters, so this "
                "run has no result to report. Adjust the model parameters, for "
                "instance a larger eps or a smaller min_samples for DBSCAN."
            )

        results: Dict[str, float] = {}
        try:
            for metric in metrics:
                score = metric.score(features, labels)
                if score is None:
                    continue
                if not math.isfinite(score):
                    log.warning(
                        "Metric %s returned a non-finite value (%s) for the "
                        "clustering. Skipping.",
                        metric.__name__,
                        score,
                    )
                    continue
                results[metric.__name__] = float(score)
        except Exception as e:
            log.exception(e)
            raise JobError(f"Metric calculation failed {e}") from e

        ctx.put_ref("metrics", {"full": results})
