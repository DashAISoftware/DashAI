"""Unit that measures a fold run with a search of its own inside each fold."""

import logging

from DashAI.back.core.enums.metrics import LevelEnum, SplitEnum
from DashAI.back.core.schema_fields import BaseSchema
from DashAI.back.job.base_job import JobError
from DashAI.back.units.context import ExecutionContext
from DashAI.back.units.fit_model_over_folds_unit import FitModelOverFoldsUnit
from DashAI.back.units.fit_scope import (
    TRIAL_SPLITS,
    goal_metric_field,
    optimizer_field,
    trial_splits_field,
)
from DashAI.back.units.splitter_scope import _splitter_field

log = logging.getLogger(__name__)


def inner_splitter_field():
    """The splitter that carves an outer fold into folds of its own.

    Required rather than optional, which is what makes this a separate unit.
    A component field wrapped in ``none_type`` is emitted as ``anyOf`` and the
    front reads ``parent`` directly off the property, so an optional one leaves
    the user with no selector at all -- the same wall that made the two
    explainer units siblings.
    """
    return _splitter_field(
        parent="FoldSplitter",
        placeholder={
            "component": "KFoldSplitter",
            "params": {"n_splits": 3, "shuffle": True, "random_state": 42},
        },
    )


class FitModelOverNestedFoldsSchema(BaseSchema):
    optimizer: optimizer_field()  # type: ignore
    goal_metric: goal_metric_field()  # type: ignore
    scored_splits: trial_splits_field()  # type: ignore
    inner_splitter: inner_splitter_field()  # type: ignore


class FitModelOverNestedFoldsUnit(FitModelOverFoldsUnit):
    """Score every outer fold with a search that never saw it.

    ``FitModelOverFoldsUnit`` plus one measurement taken before it. The
    relationship is inheritance rather than a shared mixin because that is what
    it is: everything the sibling does still happens, and this adds a step in
    front of it.

    **What the extra step is for.** In an ordinary cross-validated search, the
    same folds choose the hyperparameters and report the score, so the reported
    score is optimistic by however much the search managed to fit them. The
    nested loop measures that honestly: for each outer fold, a search is run
    from scratch on folds carved out of *that fold's training rows only*, and
    the chosen model is then scored on the outer fold's validation rows, which
    that search never saw. Those are the ``OUTER_FOLD`` rows.

    What it does **not** do is choose the hyperparameters. Each outer fold
    picks its own, and they generally differ; there is no single model to keep
    out of that loop. So the ordinary search still runs afterwards, over all
    the folds, and it is what produces the model that gets saved. The nested
    numbers are a statement about the procedure, not about the artifact.

    That also means the inner trials record nothing: their partitions belong to
    one outer fold, and rows from them would sit alongside rows describing the
    kept model as if they were comparable.
    """

    SCHEMA = FitModelOverNestedFoldsSchema

    PROVIDES = ("model", "plot_paths", "fold_metrics", "outer_fold_metrics")

    def __init__(self, **config) -> None:
        super().__init__(**config)
        self._inner_splitter = None

    def _resolve_inner_splitter(self):
        """Build the splitter that carves an outer fold, memoized on this unit."""
        if self._inner_splitter is not None:
            return self._inner_splitter

        from kink import di

        chosen = self.config["inner_splitter"]
        try:
            splitter_class = di["component_registry"][chosen["component"]]["class"]
            self._inner_splitter = splitter_class(splits_data=dict(chosen["params"]))
        except Exception as e:
            log.exception(e)
            raise JobError(
                f"Error configuring inner splitter for nested CV: {e}",
            ) from e
        return self._inner_splitter

    def execute(self, ctx: ExecutionContext) -> None:
        model = ctx.require("model")
        x_folds = ctx.require("x_folds")
        y_folds = ctx.require("y_folds")
        optimizable_parameters = ctx.require("optimizable_parameters")

        # Resolved outside the wrapper below so a splitter that cannot be built
        # is reported as that, rather than as a training failure.
        inner_splitter = self._resolve_inner_splitter()

        if optimizable_parameters:
            try:
                outer_fold_metrics = self._measure_every_outer_fold(
                    model,
                    x_folds,
                    y_folds,
                    inner_splitter,
                    optimizable_parameters,
                )
            except Exception as e:
                log.exception(e)
                raise JobError(
                    f"Model training failed {e}",
                ) from e
        else:
            # Nothing to search means nothing for the nested loop to measure:
            # every outer fold would choose the same parameters, which is what
            # the ordinary loop already reports.
            outer_fold_metrics = {}

        ctx.put_ref("outer_fold_metrics", outer_fold_metrics)

        # And then the ordinary run, which is what produces the kept model.
        super().execute(ctx)

    def _measure_every_outer_fold(
        self, model, x_folds, y_folds, inner_splitter, optimizable_parameters
    ) -> dict:
        """Search inside each outer fold, then score that fold with what it chose.

        Returns
        -------
        dict
            ``{split name: {metric name: [one score per outer fold]}}``, for
            whoever aggregates them -- the same shape and the same reason as
            the ordinary fold scores.
        """
        optimizer, goal_metric = self._resolve_search()
        scored_splits = self.config.get("scored_splits", TRIAL_SPLITS)
        outer_fold_metrics: dict = {}

        for index, (x_outer, y_outer) in enumerate(self._folds(x_folds, y_folds)):
            # Carved out of this fold's training rows alone. Its validation
            # rows are what the search will be judged on, so nothing drawn from
            # them may reach it.
            inner_x, inner_y, _ = inner_splitter.split(
                x_outer["train"], y_outer["train"]
            )

            optimizer.optimize(
                model,
                inner_x,
                inner_y,
                optimizable_parameters,
                goal_metric,
                self._score_one_inner_trial,
            )
            outer_model = optimizer.get_model()

            outer_model.x_data = x_outer
            outer_model.y_data = y_outer
            self._fit_kept_model(outer_model, x_outer, y_outer)

            for name in scored_splits:
                split = SplitEnum[name]
                results = outer_model.calculate_metrics(
                    split=split, level=LevelEnum.OUTER_FOLD, fold_index=index
                )
                if results is None:
                    results = outer_model.compute_metrics(split=split)
                if not results:
                    continue
                for metric_name, value in results.items():
                    outer_fold_metrics.setdefault(name, {}).setdefault(
                        metric_name, []
                    ).append(value)

        return outer_fold_metrics

    def _score_one_inner_trial(self, model, x_folds, y_folds, metric) -> float:
        """The objective of an inner search: the fold loop, recording nothing.

        The partitions of an inner trial belong to one outer fold. Rows written
        from them would sit in the same table as the rows describing the model
        that gets kept, indistinguishable from them and far more numerous.
        """
        return self._score_folds(model, x_folds, y_folds, metric, record=False)
