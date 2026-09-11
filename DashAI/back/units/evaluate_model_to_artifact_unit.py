"""Unit that computes a trained model's metrics and publishes them."""

import logging

from DashAI.back.core.enums.metrics import SplitEnum
from DashAI.back.core.schema_fields import (
    BaseSchema,
    enum_field,
    list_field,
    schema_field,
)
from DashAI.back.core.utils import MultilingualString
from DashAI.back.job.base_job import JobError
from DashAI.back.units.base_unit import BaseUnit
from DashAI.back.units.context import ExecutionContext

log = logging.getLogger(__name__)

DEFAULT_SPLITS = ["TRAIN", "VALIDATION", "TEST"]


class EvaluateModelToArtifactSchema(BaseSchema):
    splits: schema_field(
        list_field(enum_field(enum=DEFAULT_SPLITS)),
        placeholder=DEFAULT_SPLITS,
        description=MultilingualString(
            en="Data splits the model is evaluated on.",
            es="Particiones de datos sobre las que se evalúa el modelo.",
            pt="Partições de dados sobre as quais o modelo é avaliado.",
            de="Datenteilmengen, auf denen das Modell ausgewertet wird.",
            zh="用于评估模型的数据划分。",
        ),
        alias=MultilingualString(
            en="Splits",
            es="Particiones",
            pt="Partições",
            de="Teilmengen",
            zh="数据划分",
        ),
    )  # type: ignore


class EvaluateModelToArtifactUnit(BaseUnit):
    """Compute a trained model's metrics and publish them as data.

    The sibling of ``EvaluateModelUnit``, for a caller that has no ``Run`` row.
    That unit writes ``Metric`` rows against a foreign key to ``run.id``, so it
    cannot work without one; this returns the same numbers instead of
    persisting them, and whoever asked for them decides where they go.

    Which metrics are computed is decided by the model, not by this unit, and
    not configured here either: ``ModelFactory`` attaches the metric classes
    and the data splits to the instance, so the metrics stay configured in one
    place — where the model is built — rather than in two nodes that could
    disagree.

    Both this and ``EvaluateModelUnit`` score through
    ``BaseModel.compute_metrics``, which is what keeps them from drifting apart
    into two answers for the same model and split.
    """

    SCHEMA = EvaluateModelToArtifactSchema

    REQUIRES = ("model",)
    PROVIDES = ("metrics",)

    def execute(self, ctx: ExecutionContext) -> None:
        model = ctx.require("model")
        splits = [SplitEnum[name] for name in self.config.get("splits", DEFAULT_SPLITS)]

        metrics = {}
        try:
            for split in splits:
                scores = model.compute_metrics(split=split)
                # None means there was nothing to score -- no metrics
                # configured, or no data for this split. Recording an empty
                # entry would claim the split was evaluated and scored zero
                # metrics, which is a different statement.
                if scores is None:
                    continue
                metrics[split.value] = scores
        except Exception as e:
            log.exception(e)
            raise JobError(
                f"Metric calculation failed {e}",
            ) from e

        # A ref, not a cached object: plain numbers are exactly what survives
        # leaving the process, and what a caller records.
        ctx.put_ref("metrics", metrics)
