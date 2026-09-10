import logging
from typing import TYPE_CHECKING, Any, Dict

from kink import inject
from sqlalchemy import exc
from sqlalchemy.orm.attributes import flag_modified

from DashAI.back.core.enums.metrics import LevelEnum, SplitEnum
from DashAI.back.dependencies.database.models import (
    Dataset,
    Metric,
    ModelSession,
    Run,
)
from DashAI.back.job.base_job import BaseJob, JobError
from DashAI.back.optimizers.base_optimizer import BaseOptimizer
from DashAI.back.splitters.splits_payload import normalize_splits_payload
from DashAI.back.units.build_model_unit import BuildModelUnit
from DashAI.back.units.context import ExecutionContext
from DashAI.back.units.evaluate_model_unit import EvaluateModelUnit
from DashAI.back.units.fit_model_over_folds_unit import FitModelOverFoldsUnit
from DashAI.back.units.fit_model_over_nested_folds_unit import (
    FitModelOverNestedFoldsUnit,
)
from DashAI.back.units.fit_model_unit import FitModelUnit
from DashAI.back.units.load_dataset_unit import LoadDatasetUnit
from DashAI.back.units.prepare_and_fold_unit import PrepareAndFoldUnit
from DashAI.back.units.prepare_and_split_unit import PrepareAndSplitUnit
from DashAI.back.units.save_model_unit import SaveModelUnit

if TYPE_CHECKING:
    from sqlalchemy.orm import sessionmaker


logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)


class ModelJob(BaseJob):
    """ModelJob class to run the model training."""

    @inject
    def set_status_as_delivered(
        self, session_factory: "sessionmaker" = lambda di: di["session_factory"]
    ) -> None:
        """Set the status of the job as delivered."""
        run_id: int = self.kwargs["run_id"]

        with session_factory() as db:
            run: Run = db.get(Run, run_id)
            if not run:
                raise JobError(f"Run {run_id} does not exist in DB.")
            try:
                run.set_status_as_delivered()
                db.commit()
            except exc.SQLAlchemyError as e:
                log.exception(e)
                raise JobError(
                    "Internal database error",
                ) from e

    @inject
    def set_status_as_error(
        self, session_factory: "sessionmaker" = lambda di: di["session_factory"]
    ) -> None:
        """Set the status of the job as error."""
        run_id: int = self.kwargs.get("run_id")
        if run_id is None:
            return

        with session_factory() as db:
            run: Run = db.get(Run, run_id)
            if not run:
                return
            try:
                run.set_status_as_error()
                db.commit()
            except exc.SQLAlchemyError as e:
                log.exception(e)

    @inject
    def get_job_name(self) -> str:
        """Get a descriptive name for the job."""
        run_id = self.kwargs.get("run_id")
        if not run_id:
            return "Model Training"

        from kink import di

        session_factory = di["session_factory"]

        try:
            with session_factory() as db:
                run: Run = db.get(Run, run_id)
                if run and run.name:
                    return f"Train: {run.name}"
        except Exception:
            pass

        return f"Model Training ({run_id})"

    @inject
    def run(
        self,
    ) -> None:
        import gc
        import json

        from kink import di

        component_registry = di["component_registry"]
        session_factory = di["session_factory"]

        # Get the necessary parameters
        run_id: int = self.kwargs["run_id"]

        ctx = ExecutionContext()

        with session_factory() as db:
            run: Run = db.get(Run, run_id)
            # Without this the next line raises AttributeError on None, which
            # reaches the user as a stack trace rather than as the reason.
            if not run:
                raise JobError(f"Run {run_id} does not exist in DB.")
            run.huey_id = self.kwargs.get("huey_id", None)
            db.commit()
            self.report_progress(0.05, "Preparing data")
            try:
                try:
                    # What is left in the helper is reading the configuration
                    # this run was created with off its rows. The work that
                    # configuration describes is done by the units below.
                    preparation_results = self._prepare_dataset_and_components(
                        run_id=run_id, db=db, component_registry=component_registry
                    )
                    model_session: ModelSession = preparation_results["model_session"]
                    prepare = preparation_results["prepare_unit"]

                    LoadDatasetUnit(dataset_id=model_session.dataset_id)(ctx)

                    build_model = BuildModelUnit(
                        model={
                            "component": run.model_name,
                            "params": run.parameters,
                        },
                        train_metrics=model_session.train_metrics,
                        validation_metrics=model_session.validation_metrics,
                        test_metrics=model_session.test_metrics,
                        run_id=run_id,
                    )
                    # The download gate lives in validate(), and running it here
                    # keeps a model that cannot be trained from being reported
                    # as a splitting failure further down.
                    build_model.validate(ctx)
                except Exception as e:
                    log.exception(e)
                    raise JobError(
                        f"Error preparing dataset and components for run {run_id}: {e}",
                    ) from e

                try:
                    # Preparing the dataset for the task and partitioning it are
                    # one step: how many partitions there are and what they are
                    # called is the splitter's answer, and the pair of units
                    # differ only in which family of splitters they offer and in
                    # the shape they publish for it.
                    prepare(ctx)

                    # Only the partitions are needed here, and only to ask
                    # whether the session reserved any rows: the units read
                    # what they work on from the context themselves.
                    x = ctx.get("x") if ctx.has("x") else ctx.require("x_folds")

                    # save the obtained splits into the database
                    run.split_indexes = json.dumps(ctx.require("split_indexes"))
                except Exception as e:
                    log.exception(e)
                    raise JobError(
                        f"Error splitting the dataset for run {run_id}: {e}",
                    ) from e

                try:
                    build_model(ctx)
                except Exception as e:
                    log.exception(e)
                    raise JobError(
                        f"Error preparing dataset and components for run {run_id}: {e}",
                    ) from e

                try:
                    run.set_status_as_started()
                    db.commit()
                except exc.SQLAlchemyError as e:
                    log.exception(e)
                    raise JobError(
                        "Connection with the database failed",
                    ) from e

                strategy_class = preparation_results["evaluation_strategy_class"]
                # Which partitions a run records a score for is declared by the
                # strategy the session chose: a forecaster is not judged on the
                # dates it was fitted on, so its training partition is not in
                # this list even though metrics are configured for it.
                scored_splits = [split.name for split in strategy_class.SCORED_SPLITS]

                self.report_progress(0.2, "Training")
                try:
                    plot_paths = []

                    if getattr(strategy_class, "KIND", "holdout") == "holdout":
                        fit_model = FitModelUnit(
                            optimizer={
                                "component": run.optimizer_name,
                                "params": run.optimizer_parameters,
                            },
                            goal_metric=run.goal_metric,
                            run_id=run_id,
                            # The run names its own artifacts, which is what
                            # keeps the plot filenames of two runs apart inside
                            # the runs directory.
                            artifact_prefix=str(run_id),
                            # A trial never scores the test partition, so what
                            # it may record is whatever else the strategy scores.
                            trial_splits=[
                                name for name in scored_splits if name != "TEST"
                            ],
                        )
                        fit_model(ctx)

                        plot_paths = ctx.require("plot_paths")
                        if ctx.has("best_parameters"):
                            run.parameters = ctx.get("best_parameters")
                            flag_modified(run, "parameters")
                            db.commit()

                        self.report_progress(0.85, "Computing metrics")
                        EvaluateModelUnit(run_id=run_id, splits=scored_splits)(ctx)
                    else:
                        # Two units and not one with a flag: the nested one
                        # takes a required component field for its inner
                        # splitter, and a component field cannot be made
                        # optional without leaving the user without a selector.
                        fold_config = {
                            "optimizer": {
                                "component": run.optimizer_name,
                                "params": run.optimizer_parameters,
                            },
                            "goal_metric": run.goal_metric,
                            "run_id": run_id,
                            "artifact_prefix": str(run_id),
                            "scored_splits": [
                                name for name in scored_splits if name != "TEST"
                            ],
                        }
                        if run.nested:
                            fold_config["inner_splitter"] = {
                                "component": run.nested.get("splitter_name"),
                                "params": run.nested,
                            }
                            fit_folds = FitModelOverNestedFoldsUnit(**fold_config)
                        else:
                            fit_folds = FitModelOverFoldsUnit(**fold_config)

                        fit_folds(ctx)

                        plot_paths = ctx.require("plot_paths")
                        if ctx.has("best_parameters"):
                            run.parameters = ctx.get("best_parameters")
                            flag_modified(run, "parameters")
                            db.commit()

                        self.report_progress(0.85, "Computing metrics")
                        if ctx.has("outer_fold_metrics"):
                            # Kept at its own level: it answers a different
                            # question from the ordinary summary -- how the
                            # procedure does, rather than how this model does --
                            # and the two would be indistinguishable side by
                            # side.
                            self._aggregate_fold_metrics(
                                db,
                                run_id,
                                ctx.get("outer_fold_metrics"),
                                LevelEnum.LAST_OUTER,
                            )
                        self._aggregate_fold_metrics(
                            db, run_id, ctx.require("fold_metrics"), LevelEnum.LAST
                        )

                        # The rows the session reserved are the only ones no
                        # fold and no trial ever saw, so they are the only
                        # honest estimate left once a model is picked out of a
                        # comparison table -- and scoring them is an ordinary
                        # LAST metric, so it is the same unit a holdout run
                        # uses. Whether there is anything to score is the
                        # caller's to know: a session that reserved nothing
                        # leaves that partition empty rather than absent.
                        if len(x[-1]["test"]) > 0:
                            EvaluateModelUnit(run_id=run_id, splits=["TEST"])(ctx)
                except Exception as e:
                    log.exception(e)
                    raise JobError(
                        f"Model training and evaluation failed {e}",
                    ) from e

                try:
                    paths = plot_paths + [None] * (4 - len(plot_paths))
                    (
                        run.plot_history_path,
                        run.plot_slice_path,
                        run.plot_contour_path,
                        run.plot_importance_path,
                    ) = paths[:4]
                    db.commit()
                except Exception as e:
                    log.exception(e)
                    raise JobError(
                        f"Hyperparameter plot path saving failed {e}",
                    ) from e

                self.report_progress(0.95, "Saving model")
                SaveModelUnit(artifact_prefix=str(run_id))(ctx)

                try:
                    run.run_path = ctx.require("model_path")
                    db.commit()
                except exc.SQLAlchemyError as e:
                    log.exception(e)
                    run.set_status_as_error()
                    db.commit()
                    raise JobError(
                        "Connection with the database failed",
                    ) from e

                try:
                    run.set_status_as_finished()
                    db.commit()
                except exc.SQLAlchemyError as e:
                    log.exception(e)
                    raise JobError(
                        "Connection with the database failed",
                    ) from e
            except Exception as e:
                run.set_status_as_error()
                db.commit()
                raise e
            finally:
                ctx.clear_cache()
                gc.collect()

    @staticmethod
    def _aggregate_fold_metrics(
        db, run_id: int, fold_metrics: Dict[str, Any], level: LevelEnum
    ) -> None:
        """Summarise the per-fold scores into one row per split and metric.

        The unit that fitted the folds publishes their scores rather than
        aggregating them, because a summary row carries a standard deviation
        and a unit may not write domain rows -- the one sanctioned write in the
        domain layer has nowhere to put one. So the arithmetic and the writing
        happen here, where every other row this job persists is written.

        A single fold gets a deviation of zero rather than none: none is what
        the reserved-rows measurement carries, and the two say different
        things -- "one fold, so nothing varied" against "not a summary at all".

        Parameters
        ----------
        db : Session
            The session this job is already holding.
        run_id : int
            The run the rows belong to.
        fold_metrics : dict
            ``{split name: {metric name: [one score per fold]}}``.
        level : LevelEnum
            Where the summary goes. The ordinary fold scores summarise to
            ``LAST``; the outer folds of a nested run summarise to
            ``LAST_OUTER``, because they answer a different question and would
            be indistinguishable from the first if they shared a level.
        """
        import numpy as np

        for split_name, by_metric in fold_metrics.items():
            for metric_name, values in by_metric.items():
                if not values:
                    continue
                existing = (
                    db.query(Metric)
                    .filter_by(
                        run_id=run_id,
                        split=SplitEnum[split_name],
                        level=level,
                        name=metric_name,
                    )
                    .first()
                )
                mean = float(np.mean(values))
                deviation = float(np.std(values)) if len(values) > 1 else 0.0

                if existing:
                    existing.value = mean
                    existing.std_value = deviation
                else:
                    db.add(
                        Metric(
                            run_id=run_id,
                            split=SplitEnum[split_name],
                            level=level,
                            name=metric_name,
                            value=mean,
                            std_value=deviation,
                            step=0,
                        )
                    )
        db.commit()

    def _prepare_dataset_and_components(
        self, run_id: int, db, component_registry
    ) -> Dict[str, Any]:
        """Read the configuration this run was created with, off its rows.

        What is resolved here is what the units cannot: rows, the JSON columns
        stored on them, and the choice of which unit prepares the data. The
        work those rows describe -- loading the dataset, validating it against
        the task, separating features from targets, partitioning them and
        building the model -- belongs to the units and happens in ``run``.

        Parameters
        ----------
        run_id : int
            Identifier of the training run whose configuration must be read.
        db : object
            Database session used to retrieve the run and its model session.
        component_registry : object
            Registry used to resolve the splitter, the optimizer and the
            evaluation strategy the session names.

        Returns
        -------
        dict
            The model session, the unit that will prepare and partition the
            dataset, the evaluation strategy class, and the optimizer and goal
            metric it will be built with.

        Raises
        ------
        JobError
            If the run's session, its splits payload, its splitter, its
            optimizer or its evaluation strategy cannot be resolved.
        """

        import json

        run: Run = db.get(Run, run_id)

        model_session: ModelSession = db.get(ModelSession, run.model_session_id)
        if not model_session:
            raise JobError(
                f"Model session {run.model_session_id} does not exist in DB."
            )

        dataset: Dataset = db.get(Dataset, model_session.dataset_id)
        if not dataset:
            raise JobError(f"Dataset {model_session.dataset_id} does not exist in DB.")

        try:
            # Unpacking the JSON column is an artifact of how the row stores
            # it, not part of the split. Sessions created before the payload
            # followed the splitter schema use different keys for the seed and
            # for manual indexes.
            splits_data = json.loads(model_session.splits)
            if run.split_indexes:
                splits_data["splitted_indexes"] = json.loads(run.split_indexes)
            splits_data = normalize_splits_payload(splits_data)
        except Exception as e:
            log.exception(e)
            raise JobError(
                f"Can not load splits data from model session {model_session.id}",
            ) from e

        try:
            splitter_name = splits_data.get("splitter_name", None)
            splitter_class = component_registry[splitter_name]["class"]
        except Exception as e:
            log.exception(e)
            raise JobError(
                f"Unable to find Splitter with name {splitter_name} in registry.",
            ) from e

        # Which unit prepares the data follows from how the splitter carves it,
        # which the splitter declares. The two units publish different shapes,
        # so this is a choice of unit and not a flag on one.
        prepare_class = (
            PrepareAndFoldUnit
            if getattr(splitter_class, "PARTITIONING", "holdout") == "folds"
            else PrepareAndSplitUnit
        )
        prepare_unit = prepare_class(
            task_name=model_session.task_name,
            input_columns=model_session.input_columns,
            output_columns=model_session.output_columns,
            splitter={"component": splitter_name, "params": splits_data},
        )

        try:
            # Get the optimizer if defined
            optimizer: BaseOptimizer = None
            goal_metric = None

            if run.optimizer_name:
                run_optimizer_class = component_registry[run.optimizer_name]["class"]
                optimizer: BaseOptimizer = run_optimizer_class(
                    **run.optimizer_parameters
                )
                goal_metric = component_registry[run.goal_metric]
        except Exception as e:
            log.exception(e)
            raise JobError(
                f"Error instantiating optimizer {run.optimizer_name}, {e}",
            ) from e

        try:
            evaluation_strategy_class = component_registry[
                model_session.evaluation_strategy
            ]["class"]
        except Exception as e:
            log.exception(e)
            raise JobError(
                # string is too long, so it has to be split in two
                f"""Unable to find Evaluation Strategy with name
                {model_session.evaluation_strategy} in registry.""",
            ) from e

        return {
            "model_session": model_session,
            "prepare_unit": prepare_unit,
            "evaluation_strategy_class": evaluation_strategy_class,
            "optimizer": optimizer,
            "goal_metric": goal_metric,
        }
