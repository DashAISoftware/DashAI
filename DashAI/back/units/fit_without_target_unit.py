"""Unit that fits a model on features alone, with no target column."""

import logging

from DashAI.back.job.base_job import JobError
from DashAI.back.units.base_unit import BaseUnit
from DashAI.back.units.context import ExecutionContext

log = logging.getLogger(__name__)


class FitWithoutTargetUnit(BaseUnit):
    """Fit a model on the features of every row, with no target column.

    The counterpart of ``FitModelUnit`` for tasks whose ``REQUIRES_TARGET`` is
    False. It only calls ``model.train(features)``: nothing is held out, nothing
    is searched and nothing is scored here. The fitted instance is published
    under the same key it came in on, so the unit that scores it and the one
    that saves it see the object that was trained, not a rebuilt one.

    Named after what it does rather than after clustering: it knows nothing
    about clusters. It accepts only ``ClusteringModel`` because that is the one
    family DashAI ships that trains without a target, and there is no
    ``UnsupervisedModel`` base to accept instead. When a second family arrives,
    that base is created and ``validate`` widens to it; the name stays, because
    saved graphs persist it.
    """

    REQUIRES = ("model", "features")
    PROVIDES = ("model",)

    def validate(self, ctx: ExecutionContext) -> None:
        from DashAI.back.models.clustering_model import ClusteringModel

        model = ctx.require("model")
        if not isinstance(model, ClusteringModel):
            raise JobError(
                f"{type(model).__name__} cannot be trained without a target: "
                "only clustering models can."
            )

    def execute(self, ctx: ExecutionContext) -> None:
        model = ctx.require("model")
        features = ctx.require("features")

        try:
            model.train(features)
        except Exception as e:
            log.exception(e)
            raise JobError(f"Model training failed {e}") from e

        ctx.put("model", model)
