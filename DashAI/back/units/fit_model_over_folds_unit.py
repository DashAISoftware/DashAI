"""Unit that fits a model across cross-validation folds."""

import logging

import numpy as np

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
)

log = logging.getLogger(__name__)


class FitModelOverFoldsSchema(BaseSchema):
    optimizer: optimizer_field()  # type: ignore
    goal_metric: goal_metric_field()  # type: ignore
    scored_splits: trial_splits_field()  # type: ignore


class FitModelOverFoldsUnit(BaseUnit, ModelFitScopeMixin):
    """Fit a model once per fold, then once more on everything the folds used.

    The sibling of ``FitModelUnit``. It takes a list of partition sets rather
    than one, which is a different ``REQUIRES`` and therefore a different unit;
    everything around the fit is shared between them.

    Three things happen here, in this order, and the order is the point:

    1. If the model declares optimizable parameters, the search runs first.
       Its objective is the whole fold loop, so one trial costs k fits. That is
       what cross-validation buys and what it costs, and it is why the
       objective had to become something the caller supplies rather than
       something the optimizer does.
    2. Every fold is fitted and scored, and a ``FOLD`` metric row is written
       for it. Those rows are what the fold charts and the statistical tests
       read, and they are indexed from zero without gaps -- repeated
       cross-validation buckets them by integer division, so a gap silently
       moves a fold into the wrong repetition.
    3. The model that gets kept is fitted on every row the folds could use,
       and left pointing at that partition set. Scoring it against the rows the
       session reserved is not done here: that is a ``LAST`` metric like any
       other, so it is ``EvaluateModelUnit``'s, the same unit a holdout run
       uses -- and the caller is the one that knows whether anything was
       reserved to score against.

    **The per-fold scores are published rather than aggregated here.** Turning
    them into a mean and a deviation means writing ``Metric`` rows that carry a
    ``std_value``, and a unit may not write domain rows -- the one sanctioned
    write in the domain layer, ``BaseModel._save_metrics``, has nowhere to put
    a deviation. Whoever asked for the fit aggregates and persists.

    Nested cross-validation is not here either: its inner splitter is a
    required component field, and a component field cannot be made optional
    without leaving the user without a selector, so it is a further sibling
    rather than a flag on this one.
    """

    SCHEMA = FitModelOverFoldsSchema

    REQUIRES = (
        "model",
        "factory",
        "optimizable_parameters",
        "model_parameters",
        "x_folds",
        "y_folds",
    )
    PROVIDES = ("model", "plot_paths", "fold_metrics")
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
        x_folds = ctx.require("x_folds")
        y_folds = ctx.require("y_folds")
        optimizable_parameters = ctx.require("optimizable_parameters")

        plot_paths = []
        try:
            if optimizable_parameters:
                # Every read of the context happens in this file rather than in
                # the shared helper: the contract audit parses it, so a require
                # moved out makes a declared key look unread.
                model, best_parameters, plot_paths = self._search(
                    model,
                    x_folds,
                    y_folds,
                    optimizable_parameters,
                    ctx.require("factory"),
                    ctx.require("model_parameters"),
                    self.config["run_id"],
                    self.config["artifact_prefix"],
                    self._score_one_trial,
                )
                ctx.put_ref("best_parameters", best_parameters)

            fold_metrics = self._score_every_fold(model, x_folds, y_folds)

            # The model that gets kept is fitted last, on every row the folds
            # could use, and is left pointing at that partition set -- which is
            # what whoever scores it afterwards will be scoring.
            model.x_data = x_folds[-1]
            model.y_data = y_folds[-1]
            self._fit_kept_model(model, x_folds[-1], y_folds[-1])
        except Exception as e:
            log.exception(e)
            raise JobError(
                f"Model training failed {e}",
            ) from e

        ctx.put("model", model)
        ctx.put_ref("plot_paths", plot_paths)
        ctx.put_ref("fold_metrics", fold_metrics)

    # ----------------------------------------------------------------- #
    # The three things, one method each
    # ----------------------------------------------------------------- #

    def _score_one_trial(self, model, x_folds, y_folds, metric) -> float:
        """Fit and score every fold, and return the mean, for one trial.

        This is what the optimizer measures, and it is the whole difference
        between this unit and its sibling: there, a trial is one fit; here it
        is k of them. The optimizer passes the partitions through without
        looking at them, so it does not have to know which.

        One row per split is written for the trial, holding the mean over its
        folds -- not one row per fold. The folds of a trial measure a
        hyperparameter setting rather than the model that gets kept, so
        recording each of them would bury the rows that describe it, and the
        live chart that watches a search wants one point per trial anyway.

        The objective is scored directly rather than read out of those means,
        because the goal metric is not necessarily one of the metrics the
        session configured for the validation partition.

        Returns
        -------
        float
            The mean of the goal metric over the folds, which is the objective.
        """
        scored_splits = self.config.get("scored_splits", TRIAL_SPLITS)
        scores = []
        accumulated: dict = {}

        for x_fold, y_fold in self._folds(x_folds, y_folds):
            # Pointed at the fold it is about to be fitted on, the same as in
            # the scoring loop. Nothing here reads it back, but the model is
            # expected to carry the data it was last fitted on -- that is what
            # the check after the search asserts, and what anything scoring it
            # afterwards relies on.
            model.x_data = x_fold
            model.y_data = y_fold
            self._fit_kept_model(model, x_fold, y_fold)
            predictions = model.predict(x_fold["validation"])
            expected = model.prepare_output(y_fold["validation"], is_fit=False)
            scores.append(metric.score(expected, predictions))

            for name in scored_splits:
                results = model.compute_metrics(split=SplitEnum[name])
                for metric_name, value in (results or {}).items():
                    accumulated.setdefault(name, {}).setdefault(metric_name, []).append(
                        value
                    )

        self._record_trial(model, accumulated)
        return float(np.mean(scores))

    @staticmethod
    def _record_trial(model, accumulated: dict) -> None:
        """Write one metric row per split for this trial, holding its mean.

        Guarded on the run, which ``_save_metrics`` does not do for itself: a
        caller with no run -- a pipeline -- would otherwise write rows against
        a foreign key pointing at nothing, and they insert without complaint
        because the database has no enforcement to refuse them. That is the
        failure mode a metrics unit already exists to avoid, so it is refused
        here too rather than repeated.
        """
        if not getattr(model, "run_id", None):
            return

        for split_name, by_metric in accumulated.items():
            averaged = {
                metric_name: float(np.mean(values))
                for metric_name, values in by_metric.items()
            }
            if averaged:
                model._save_metrics(
                    results=averaged,
                    split=SplitEnum[split_name],
                    level=LevelEnum.TRIAL,
                )

    def _score_every_fold(self, model, x_folds, y_folds) -> dict:
        """Fit and score each fold, writing its rows and keeping its numbers.

        Returns
        -------
        dict
            ``{split name: [one score per fold]}``, in fold order, for whoever
            aggregates them. A split with no metrics configured is absent
            rather than present and empty: the two are different statements.
        """
        scored_splits = self.config.get("scored_splits", TRIAL_SPLITS)
        fold_metrics: dict = {}

        for index, (x_fold, y_fold) in enumerate(self._folds(x_folds, y_folds)):
            # The metric methods read the data off the instance to decide what
            # they are scoring, so it follows the iteration.
            model.x_data = x_fold
            model.y_data = y_fold
            self._fit_kept_model(model, x_fold, y_fold)

            for name in scored_splits:
                split = SplitEnum[name]
                # calculate_metrics hands back what it wrote, so the split is
                # scored once rather than once for the row and once for the
                # number. It writes nothing, and returns nothing, when there is
                # no run to write against -- a pipeline -- and the numbers are
                # wanted there too, hence the fallback.
                results = model.calculate_metrics(
                    split=split, level=LevelEnum.FOLD, fold_index=index
                )
                if results is None:
                    results = model.compute_metrics(split=split)
                if not results:
                    continue
                for metric_name, value in results.items():
                    fold_metrics.setdefault(name, {}).setdefault(
                        metric_name, []
                    ).append(value)

        return fold_metrics

    def _fit_kept_model(self, model, x, y) -> None:
        """Fit on the training partition, never handing over the validation one.

        A fold is scored on the rows it held back from its own training, so
        letting the fit watch them would measure it on data it was allowed to
        see -- and nothing raises when that happens, the score simply comes out
        better than the model deserves. Unlike the holdout sibling this is not
        configurable, because there is no reading of a fold under which it
        would be right.
        """
        self._fit(model, x, y, with_validation=False)

    @staticmethod
    def _folds(x_folds, y_folds):
        """Pair up the folds, leaving out the entry that is not one.

        A fold splitter returns one entry per fold plus a trailing entry
        holding every row the folds could use and the rows reserved from them.
        That last one fits the model that gets kept; it is not a fold and is
        never scored as one.
        """
        return zip(x_folds[:-1], y_folds[:-1], strict=True)
