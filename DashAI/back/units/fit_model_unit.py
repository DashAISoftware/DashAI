"""Unit that fits a model on one set of partitions, optionally searching."""

import logging

from DashAI.back.core.enums.metrics import LevelEnum, SplitEnum
from DashAI.back.core.schema_fields import BaseSchema
from DashAI.back.job.base_job import JobError
from DashAI.back.units.base_unit import BaseUnit
from DashAI.back.units.context import ExecutionContext
from DashAI.back.units.fit_scope import (
    TRIAL_SPLITS,
    ModelFitScopeMixin,
    goal_metric_field,
    optimizer_field,
    trial_splits_field,
    validation_during_fit_field,
)

log = logging.getLogger(__name__)


class FitModelSchema(BaseSchema):
    optimizer: optimizer_field()  # type: ignore
    goal_metric: goal_metric_field()  # type: ignore
    trial_splits: trial_splits_field()  # type: ignore
    validation_during_fit: validation_during_fit_field()  # type: ignore


class FitModelUnit(BaseUnit, ModelFitScopeMixin):
    """Train a model, running a hyperparameter search when there is one to run.

    Hyperparameter optimization is a fitting strategy rather than a separate
    step: it returns a fitted model, and the trial plots are a by-product only
    that branch produces. Both paths therefore live in this unit.

    ``validate`` resolves the optimizer and the goal metric so an impossible
    configuration is rejected before the job reports that training started.

    The sibling for cross-validation is ``FitModelOverFoldsUnit``: it takes a
    list of partition sets rather than one, which is a different ``REQUIRES``
    and therefore a different unit. What surrounds the fit is shared between
    them; only the objective the search measures, and what happens once the
    search is over, is written here.
    """

    SCHEMA = FitModelSchema

    # run_id and artifact_prefix are configuration, not context: no unit
    # publishes them, so nothing upstream could ever satisfy them as REQUIRES.
    # See the artifact_prefix section of DAG_ENGINE.md.
    REQUIRES = (
        "model",
        "factory",
        "optimizable_parameters",
        "model_parameters",
        "x",
        "y",
    )
    PROVIDES = ("model", "plot_paths")
    RUNTIME_PARAMS = ("run_id", "artifact_prefix")

    def __init__(self, **config) -> None:
        super().__init__(**config)
        self._optimizer = None
        self._goal_metric = None

    def validate(self, ctx: ExecutionContext) -> None:
        # ctx.require, not ctx.get: an absent key means BuildModelUnit has not
        # run yet, which is a call-order mistake rather than a model with
        # nothing to optimize.
        self._validate_search(ctx.require("optimizable_parameters"))

    def execute(self, ctx: ExecutionContext) -> None:
        model = ctx.require("model")
        x = ctx.require("x")
        y = ctx.require("y")
        optimizable_parameters = ctx.require("optimizable_parameters")

        # The model is pointed at the data it is about to be fitted on, here
        # rather than where it was built: the metric methods read these
        # attributes off the instance to decide what they are scoring.
        model.x_data = x
        model.y_data = y

        plot_paths = []
        try:
            if not self._will_search(optimizable_parameters):
                self._fit_kept_model(model, x, y)
            else:
                # Every read of the context happens here rather than in the
                # shared helper: the contract audit parses this file, so a
                # require moved out of it makes a declared key look unread.
                model, best_parameters, plot_paths = self._search(
                    model,
                    x,
                    y,
                    optimizable_parameters,
                    ctx.require("factory"),
                    # ctx.require already hands back an isolated copy of the
                    # stored parameter tree, so writing the best values into it
                    # cannot touch the Run row it came from.
                    ctx.require("model_parameters"),
                    self.config["run_id"],
                    self.config["artifact_prefix"],
                    self._score_one_trial,
                )
                ctx.put_ref("best_parameters", best_parameters)
        except Exception as e:
            log.exception(e)
            raise JobError(
                f"Model training failed {e}",
            ) from e

        ctx.put("model", model)
        ctx.put_ref("plot_paths", plot_paths)

    def _fit_kept_model(self, model, x, y) -> None:
        """Fit the model that gets kept, on the partitions it was given."""
        self._fit(model, x, y, self.config.get("validation_during_fit", True))

    def _score_one_trial(self, model, x, y, metric) -> float:
        """Fit the model once and score it, for one point of the search.

        This is what the optimizer measures. It used to be the optimizer's own
        business: the objective fitted and scored inline, and the sixth
        argument of ``optimize`` was the task. It is now a callable the caller
        supplies, which is the change that lets the search be reused over
        anything that can be fitted and scored -- a single split here, a whole
        set of folds in the sibling -- without the optimizer knowing which.

        The trial metrics are written here rather than by the optimizer for the
        same reason: what counts as a scored partition is a property of the
        thing being fitted, not of the search. Which ones those are is
        configured, because it is not always the same as which ones have
        metrics: a forecaster has training metrics and still must not be judged
        on the dates it was fitted on, since an in-sample fit statistic is not
        comparable with a forecast. A partition left in the list but with no
        metrics configured writes nothing anyway -- ``calculate_metrics`` finds
        nothing to score and returns.

        Parameters
        ----------
        model : BaseModel
            The instance the optimizer has just set this trial's parameters on.
        x, y : DatasetDict
            The partitions this fit may use.
        metric : BaseMetric
            The metric class the search is optimizing, already unwrapped from
            its registry entry by the optimizer.

        Returns
        -------
        float
            The score on the validation partition, which is the objective.
        """
        self._fit_kept_model(model, x, y)

        for name in self.config.get("trial_splits", TRIAL_SPLITS):
            model.calculate_metrics(split=SplitEnum[name], level=LevelEnum.TRIAL)

        predictions = model.predict(x["validation"])
        expected = model.prepare_output(y["validation"], is_fit=False)
        return metric.score(expected, predictions)
