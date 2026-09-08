import logging
from typing import TYPE_CHECKING, Any, Dict, List

from kink import inject
from sqlalchemy import exc

from DashAI.back.core.enums.status import SessionPreprocessingStatus
from DashAI.back.dependencies.database.models import ModelSession, Run
from DashAI.back.dependencies.downloads.nested import missing_downloads
from DashAI.back.evaluation.base_evaluation_strategy import BaseEvaluationStrategy
from DashAI.back.job.base_job import BaseJob, JobError
from DashAI.back.job.dataset_split_utils import load_dataset_and_splitter
from DashAI.back.job.session_preprocessing_job import (
    get_real_input_output_columns,
    load_preprocessed_reference_dataset,
    load_preprocessed_session_data,
)
from DashAI.back.metrics.base_metric import BaseMetric
from DashAI.back.models.model_factory import ModelFactory
from DashAI.back.optimizers.base_optimizer import BaseOptimizer
from DashAI.back.splitters.base_splitter import BaseSplitter

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

        with session_factory() as db:
            run: Run = db.get(Run, run_id)
            run.huey_id = self.kwargs.get("huey_id", None)
            db.commit()
            self.report_progress(0.05, "Preparing data")
            try:
                try:
                    # Get the dataset and components prepared for the model training
                    preparation_results = self._prepare_dataset_and_components(
                        run_id=run_id, db=db, component_registry=component_registry
                    )
                except Exception as e:
                    log.exception(e)
                    raise JobError(
                        f"Error preparing dataset and components for run {run_id}: {e}",
                    ) from e

                try:
                    # Get splits from the splitter
                    splitter: BaseSplitter = preparation_results["splitter"]
                    # Get the dataset splits between input columns and output column
                    X, Y = preparation_results["X"], preparation_results["Y"]

                    # Get x,y but now splitted with train, validation and test indexes
                    # each one, and the indexes used for the splits
                    x, y, splits = splitter.split(X, Y)

                    # save the obtained splits into the database
                    run.split_indexes = json.dumps(splits)
                except Exception as e:
                    log.exception(e)
                    raise JobError(
                        f"Error splitting the dataset for run {run_id}: {e}",
                    ) from e

                try:
                    # When the session has converters, its dataset was
                    # already fit/transformed once by SessionPreprocessingJob
                    # (see session_preprocessing_job.py) — the split computed
                    # above on the raw dataset is only kept for
                    # run.split_indexes (explainer_job.py needs it later);
                    # the actual training data comes from disk instead.
                    # (preprocessing-finished is already checked in
                    # _prepare_dataset_and_components, before this point.)
                    model_session: ModelSession = preparation_results["model_session"]
                    if model_session.converters:
                        self.report_progress(0.15, "Loading preprocessed data")
                        x, y = load_preprocessed_session_data(model_session)
                except JobError:
                    raise
                except Exception as e:
                    log.exception(e)
                    raise JobError(
                        f"Error loading preprocessed session data for run "
                        f"{run_id}: {e}",
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

                    evaluation_estrategy: BaseEvaluationStrategy = preparation_results[
                        "evaluation_strategy"
                    ]

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
                    model.save(run_path)
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
                gc.collect()

    def _prepare_dataset_and_components(
        self, run_id: int, db, component_registry
    ) -> Dict[str, Any]:
        """Prepare the dataset, task, splitter, metrics, model, and evaluation strategy.

        This helper resolves the persisted training configuration for a run,
        loads the associated dataset from disk, prepares it for the selected
        task, instantiates the required components from the component registry,
        and builds the model factory together with the evaluation strategy.

        Parameters
        ----------
        run_id : int
            Identifier of the training run whose configuration and artifacts must
            be loaded.
        db : object
            Database access object used to retrieve the run, model session, and
            related persisted entities.
        component_registry : object
            Registry containing the available task, splitter, metric, model,
            optimizer, and evaluation strategy implementations.

        Returns
        -------
        dict
            A dictionary containing the prepared input and output datasets, the
            instantiated splitter, and the evaluation strategy.

        Raises
        ------
        JobError
            If the run, model session, dataset, task, splitter, metrics, model,
            optimizer, or evaluation strategy cannot be resolved or instantiated.
        """

        import json

        run: Run = db.get(Run, run_id)

        # Get the model session from the database
        model_session: ModelSession = db.get(ModelSession, run.model_session_id)
        if not model_session:
            raise JobError(
                f"Model session {run.model_session_id} does not exist in DB."
            )

        if (
            model_session.converters
            and model_session.preprocessing_status
            != SessionPreprocessingStatus.FINISHED
        ):
            raise JobError(
                f"Model session {model_session.id} preprocessing is not "
                f"finished (status={model_session.preprocessing_status}); "
                "cannot train a Run until preprocessing finishes."
            )

        splitted_indexes = json.loads(run.split_indexes) if run.split_indexes else None
        X, Y, splitter, task, prepared_dataset = load_dataset_and_splitter(
            model_session, db, component_registry, splitted_indexes=splitted_indexes
        )

        # `model_session.input_columns`/`output_columns` are always atom
        # dicts (never plain strings) since the group-atoms feature; the
        # real column names are needed here regardless of whether this
        # session has converters (see `get_real_input_output_columns`).
        _real_input_columns, real_output_columns = get_real_input_output_columns(
            model_session
        )

        try:
            if model_session.converters:
                # The raw dataset never had any column a converter added or
                # renamed (e.g. `LabelEncoder` appending `le_<col>`), so
                # `prepared_dataset` above may only be the placeholder
                # `load_dataset_and_splitter` falls back to in that case —
                # it can't answer `num_labels` for a converter-produced
                # output column. Validate/type the session's *actual*
                # training data (the preprocessed reference partition)
                # instead, purely for this computation.
                #
                # `input_columns=[]` here is deliberate: a converter that
                # only transforms *inputs* in place (e.g. `StandardScaler`)
                # doesn't reliably preserve full DashAI type metadata for
                # every passed-through column once saved to disk (a
                # separate, pre-existing gap in how partitions persist
                # types) — but this computation only ever needs the
                # *output* column's type, and both task classes' input
                # cardinality is "n", so skipping input validation here
                # changes nothing this call cares about.
                reference_dataset = load_preprocessed_reference_dataset(model_session)
                reference_prepared = task.prepare_for_task(
                    dataset=reference_dataset,
                    input_columns=[],
                    output_columns=real_output_columns,
                )
                n_labels = task.num_labels(reference_prepared, real_output_columns[0])
            else:
                n_labels = task.num_labels(prepared_dataset, real_output_columns[0])
        except Exception as e:
            log.exception(e)
            raise JobError(
                f"""Can not compute number of labels for
                Task {model_session.task_name}""",
            ) from e

        try:
            # Get metrics from model session
            train_metrics: List[BaseMetric] = [
                component_registry[m]["class"] for m in model_session.train_metrics
            ]
            validation_metrics: List[BaseMetric] = [
                component_registry[m]["class"] for m in model_session.validation_metrics
            ]
            test_metrics: List[BaseMetric] = [
                component_registry[m]["class"] for m in model_session.test_metrics
            ]
        except Exception as e:
            log.exception(e)
            raise JobError(
                "Unable to find metrics associated with"
                f"Task {model_session.task_name} in registry",
            ) from e

        try:
            # Get the model class from the registry
            run_model_class = component_registry[run.model_name]["class"]
        except Exception as e:
            log.exception(e)
            raise JobError(
                f"Unable to find Model with name {run.model_name} in registry.",
            ) from e

        # Make sure the model (and any nested components) are downloaded
        # before attempting to train, otherwise fail fast with a clear error.
        if getattr(run_model_class, "REQUIRES_DOWNLOAD", False) and not (
            run_model_class.is_downloaded()
        ):
            raise JobError(
                f"Model {run.model_name} is not downloaded. "
                "Download it before training."
            )
        nested_missing = missing_downloads(run.parameters, component_registry)
        if nested_missing:
            names = ", ".join(m["name"] for m in nested_missing)
            raise JobError(
                "These components are not downloaded. "
                f"Download them before training: {names}."
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
            # Instantiate the model using the ModelFactory
            # and get the optimizable parameters
            factory = ModelFactory(
                model=run_model_class,
                params=run.parameters,
                run_id=run_id,
                train_metrics=train_metrics,
                validation_metrics=validation_metrics,
                test_metrics=test_metrics,
                n_labels=n_labels,
            )
        except Exception as e:
            log.exception(e)
            raise JobError(
                f"Unable to instantiate model using run {run_id}",
            ) from e

        try:
            # Get the evaluation strategy for the model session
            evaluation_strategy: BaseEvaluationStrategy = component_registry[
                model_session.evaluation_strategy
            ]["class"](
                factory=factory,
                optimizer=optimizer,
                goal_metric=goal_metric,
            )
        except Exception as e:
            log.exception(e)
            raise JobError(
                # string is too long, so it has to be split in two
                f"""Unable to find Evaluation Strategy with name
                {model_session.evaluation_strategy} in registry.""",
            ) from e

        return {
            "X": X,
            "Y": Y,
            "splitter": splitter,
            "evaluation_strategy": evaluation_strategy,
            "model_session": model_session,
        }
