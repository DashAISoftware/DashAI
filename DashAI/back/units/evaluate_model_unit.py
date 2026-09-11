"""Unit that computes and stores the final metrics of a trained model."""

import logging

from DashAI.back.core.enums.metrics import LevelEnum, SplitEnum
from DashAI.back.core.schema_fields import (
    BaseSchema,
    enum_field,
    list_field,
    schema_field,
)
from DashAI.back.core.utils import MultilingualString
from DashAI.back.dependencies.database.models import Metric
from DashAI.back.job.base_job import JobError
from DashAI.back.units.base_unit import BaseUnit
from DashAI.back.units.context import ExecutionContext

log = logging.getLogger(__name__)

DEFAULT_SPLITS = ["TRAIN", "VALIDATION", "TEST"]


class EvaluateModelSchema(BaseSchema):
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


class EvaluateModelUnit(BaseUnit):
    """Compute the final metrics of a trained model, once per split.

    The unit is idempotent: a split whose final metrics were already logged
    (for instance by a model that evaluates itself while training) is skipped.

    Which metrics are computed is decided by the model, not by this unit:
    ``ModelFactory`` attaches the metric classes to the model instance, and
    ``BaseModel.calculate_metrics`` is ``final``. That method persists the
    rows through a session of its own, so these writes are not part of the
    transaction the calling job controls.

    **This unit needs a real ``Run`` row and cannot be used without one.**
    Everything it does is write ``Metric`` rows against a foreign key to
    ``run.id``, so there is nothing left for it to do when there is no run.
    ``validate`` refuses a missing run id rather than letting it through,
    because the failure would otherwise be silent in both directions: the
    idempotency query below would match no row whatever was already logged,
    and ``calculate_metrics`` no-ops on a model with no run — so the unit
    would report success having written nothing at all.

    A caller that wants a model's metrics *without* a run wants a different
    unit, one that returns them instead of persisting them.
    """

    SCHEMA = EvaluateModelSchema

    # run_id is configuration, not context: no unit publishes it.
    REQUIRES = ("model",)
    RUNTIME_PARAMS = ("run_id",)

    def validate(self, ctx: ExecutionContext) -> None:
        if self.config["run_id"] is None:
            raise JobError(
                "Metrics can only be logged against a run, and this one has no "
                "run id. Use a unit that returns the metrics instead of writing "
                "them if there is no run to attach them to."
            )

    def execute(self, ctx: ExecutionContext) -> None:
        from kink import di

        session_factory = di["session_factory"]

        model = ctx.require("model")
        # validate() already refused a None here, which is what keeps the
        # idempotency query below from matching no row regardless of what was
        # actually logged.
        run_id = self.config["run_id"]
        splits = [SplitEnum[name] for name in self.config.get("splits", DEFAULT_SPLITS)]

        try:
            for split in splits:
                with session_factory() as db:
                    already_logged = (
                        db.query(Metric)
                        .filter_by(run_id=run_id, split=split, level=LevelEnum.LAST)
                        .first()
                    )
                if already_logged:
                    continue

                model.calculate_metrics(split=split, level=LevelEnum.LAST)
        except Exception as e:
            log.exception(e)
            raise JobError(
                f"Metric calculation failed {e}",
            ) from e
