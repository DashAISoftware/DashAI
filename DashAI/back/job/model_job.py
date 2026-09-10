import logging
from typing import TYPE_CHECKING, Any, Dict

from kink import inject
from sqlalchemy import exc

from DashAI.back.core.atomic import atomic_save_path
from DashAI.back.dependencies.database.models import Dataset, ModelSession, Run
from DashAI.back.evaluation.base_evaluation_strategy import BaseEvaluationStrategy
from DashAI.back.job.base_job import BaseJob, JobError
from DashAI.back.optimizers.base_optimizer import BaseOptimizer
from DashAI.back.splitters.splits_payload import normalize_splits_payload
from DashAI.back.units.build_model_unit import BuildModelUnit
from DashAI.back.units.context import ExecutionContext
from DashAI.back.units.load_dataset_unit import LoadDatasetUnit
from DashAI.back.units.prepare_and_fold_unit import PrepareAndFoldUnit
from DashAI.back.units.prepare_and_split_unit import PrepareAndSplitUnit

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
        import os

        from kink import di

        component_registry = di["component_registry"]
        session_factory = di["session_factory"]
        config = di["config"]

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

                    x = ctx.get("x") if ctx.has("x") else ctx.require("x_folds")
                    y = ctx.get("y") if ctx.has("y") else ctx.require("y_folds")

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

                self.report_progress(0.2, "Training")
                try:
                    # Hyperparameter Tunning
                    plot_paths = []

                    # Built here rather than in the helper because it takes
                    # the factory the build unit produced.
                    strategy_class = preparation_results["evaluation_strategy_class"]
                    evaluation_estrategy: BaseEvaluationStrategy = strategy_class(
                        factory=ctx.require("factory"),
                        optimizer=preparation_results["optimizer"],
                        goal_metric=preparation_results["goal_metric"],
                    )

                    evaluation_estrategy.set_progress_reporter(self.report_progress)
                    model, plot_paths = evaluation_estrategy.execute(
                        x=x,
                        y=y,
                        run=run,
                        db=db,
                    )
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
                try:
                    run_path = os.path.join(config["RUNS_PATH"], str(run.id))
                    with atomic_save_path(run_path) as tmp_run_path:
                        model.save(str(tmp_run_path))
                except Exception as e:
                    log.exception(e)
                    raise JobError(
                        "Model saving failed",
                    ) from e

                try:
                    run.run_path = run_path
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
