import json
import logging
import os
import pickle
from typing import List

from kink import inject
from sqlalchemy import exc
from sqlalchemy.orm import Session

from DashAI.back.dataloaders.classes.dashai_dataset import (
    DashAIDataset,
    load_dataset,
    select_columns,
    update_dataset_splits,
)
from DashAI.back.dependencies.database.models import Dataset, Experiment, Run
from DashAI.back.dependencies.registry import ComponentRegistry
from DashAI.back.job.base_job import BaseJob, JobError
from DashAI.back.metrics import BaseMetric
from DashAI.back.models import BaseModel
from DashAI.back.optimizers import BaseOptimizer
from DashAI.back.tasks import BaseTask

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)


class ModelJob(BaseJob):
    """ModelJob class to run the model training."""

    def set_status_as_delivered(self) -> None:
        """Set the status of the job as delivered."""
        run_id: int = self.kwargs["run_id"]
        db: Session = self.kwargs["db"]

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
    def run(
        self,
        component_registry: ComponentRegistry = lambda di: di["component_registry"],
        config=lambda di: di["config"],
    ) -> None:
        from DashAI.back.api.api_v1.endpoints.components import (
            _intersect_component_lists,
        )

        # Get the necessary parameters
        run_id: int = self.kwargs["run_id"]
        db: Session = self.kwargs["db"]

        run: Run = db.get(Run, run_id)
        try:
            # Get the experiment, dataset, task, metrics and splits
            experiment: Experiment = db.get(Experiment, run.experiment_id)
            if not experiment:
                raise JobError(f"Experiment {run.experiment_id} does not exist in DB.")
            dataset: Dataset = db.get(Dataset, experiment.dataset_id)
            if not dataset:
                raise JobError(f"Dataset {experiment.dataset_id} does not exist in DB.")

            try:
                loaded_dataset: DashAIDataset = load_dataset(
                    f"{dataset.file_path}/dataset"
                )
            except Exception as e:
                log.exception(e)
                raise JobError(
                    f"Can not load dataset from path {dataset.file_path}",
                ) from e

            try:
                task: BaseTask = component_registry[experiment.task_name]["class"]()
            except Exception as e:
                log.exception(e)
                raise JobError(
                    f"Unable to find Task with name {experiment.task_name} in registry",
                ) from e

            try:
                # Get all the metrics
                all_metrics = {
                    component_dict["name"]: component_dict
                    for component_dict in component_registry.get_components_by_types(
                        select="Metric"
                    )
                }
                # Get the intersection between the metrics and the task
                # related components
                selected_metrics = _intersect_component_lists(
                    all_metrics,
                    component_registry.get_related_components(experiment.task_name),
                )
                metrics: List[BaseMetric] = [
                    metric["class"] for metric in selected_metrics.values()
                ]
            except Exception as e:
                log.exception(e)
                raise JobError(
                    "Unable to find metrics associated with"
                    f"Task {experiment.task_name} in registry",
                ) from e

            try:
                splits = json.loads(experiment.splits)
                if splits["has_changed"]:
                    new_splits = {
                        "train": splits["train"],
                        "test": splits["test"],
                        "validation": splits["validation"],
                    }
                    loaded_dataset = update_dataset_splits(
                        loaded_dataset,
                        new_splits,
                        splits["is_random"],
                    )
                prepared_dataset = task.prepare_for_task(
                    loaded_dataset, experiment.output_columns
                )
                x, y = select_columns(
                    prepared_dataset,
                    experiment.input_columns,
                    experiment.output_columns,
                )
            except Exception as e:
                log.exception(e)
                raise JobError(
                    f"""Can not prepare Dataset {dataset.id}
                    for Task {experiment.task_name}""",
                ) from e

            try:
                run_model_class = component_registry[run.model_name]["class"]
            except Exception as e:
                log.exception(e)
                raise JobError(
                    f"Unable to find Model with name {run.model_name} in registry.",
                ) from e
            try:
                if experiment.task_name not in [
                    "TextClassificationTask",
                    "TabularClassificationTask",
                ]:
                    run_fixed_parameters = run.parameters
                    run_optimizable_parameters = {}
                    model: BaseModel = run_model_class(**run_fixed_parameters)
                elif experiment.task_name == "TextClassificationTask":
                    # Divide the parameters in fixed and optimizable
                    run_fixed_parameters = {
                        key: (
                            parameter["fixed_value"]
                            if isinstance(parameter, dict) and "optimize" in parameter
                            else parameter
                        )
                        for key, parameter in run.parameters["tabular_classifier"][
                            "properties"
                        ]["params"]["comp"]["params"].items()
                        if (
                            isinstance(parameter, dict)
                            and parameter.get("optimize") is False
                        )
                        or isinstance(parameter, (bool, str))
                    }
                    run_optimizable_parameters = {
                        key: (parameter["lower_bound"], parameter["upper_bound"])
                        for key, parameter in run.parameters["tabular_classifier"][
                            "properties"
                        ]["params"]["comp"]["params"].items()
                        if (
                            isinstance(parameter, dict)
                            and parameter.get("optimize") is True
                        )
                    }
                    submodel: BaseModel = component_registry[
                        run.parameters["tabular_classifier"]["properties"]["params"][
                            "comp"
                        ]["component"]
                    ]["class"](**run_fixed_parameters)
                    model: BaseModel = run_model_class(submodel, **run.parameters)

                else:
                    run_fixed_parameters = {
                        key: (
                            parameter["fixed_value"]
                            if isinstance(parameter, dict) and "optimize" in parameter
                            else parameter
                        )
                        for key, parameter in run.parameters.items()
                        if (
                            isinstance(parameter, dict)
                            and parameter.get("optimize") is False
                        )
                        or isinstance(parameter, (bool, str))
                    }
                    run_optimizable_parameters = {
                        key: (parameter["lower_bound"], parameter["upper_bound"])
                        for key, parameter in run.parameters.items()
                        if (
                            isinstance(parameter, dict)
                            and parameter.get("optimize") is True
                        )
                    }
                    model: BaseModel = run_model_class(**run_fixed_parameters)
            except Exception as e:
                log.exception(e)
                raise JobError(
                    f"Unable to instantiate model using run {run_id}",
                ) from e
            if experiment.task_name in [
                "TextClassificationTask",
                "TabularClassificationTask",
            ]:
                try:
                    # Optimizer configuration
                    run_optimizer_class = component_registry[run.optimizer_name][
                        "class"
                    ]
                except Exception as e:
                    log.exception(e)
                    raise JobError(
                        f"Unable to find Model with name {run.optimizer_name} in "
                        "registry.",
                    ) from e

                try:
                    run.optimizer_parameters["metric"] = selected_metrics[
                        run.optimizer_parameters["metric"]
                    ]
                except Exception as e:
                    log.exception(e)
                    raise JobError(
                        "Metric is not compatible with the Task",
                    ) from e
                try:
                    optimizer: BaseOptimizer = run_optimizer_class(
                        **run.optimizer_parameters
                    )
                except Exception as e:
                    log.exception(e)
                    raise JobError(
                        "Optimizer parameters are not compatible with the optimizer",
                    ) from e
            try:
                run.set_status_as_started()
                db.commit()
            except exc.SQLAlchemyError as e:
                log.exception(e)
                raise JobError(
                    "Connection with the database failed",
                ) from e
            try:
                # Hyperparameter Tunning
                if not run_optimizable_parameters:
                    model.fit(x["train"], y["train"])
                else:
                    optimizer.optimize(
                        model,
                        x,
                        y,
                        run_optimizable_parameters,
                        experiment.task_name,
                    )
                    model = optimizer.get_model()
                    # Generate hyperparameter plot
                    X, Y = optimizer.get_metrics()
                    plot = optimizer.create_plot(X, Y)
                    plot_filename = f"hyperparameter_optimization_plot_{run_id}.pickle"
                    plot_path = os.path.join(config["RUNS_PATH"], plot_filename)
                    with open(plot_path, "wb") as file:
                        pickle.dump(plot, file)
            except Exception as e:
                log.exception(e)
                raise JobError(
                    "Model training failed",
                ) from e
            if run_optimizable_parameters != {}:
                try:
                    run.plot_path = plot_path
                    db.commit()
                except Exception as e:
                    log.exception(e)
                    raise JobError(
                        "Hyperparameter plot path saving failed",
                    ) from e
            try:
                run.set_status_as_finished()
                db.commit()
            except exc.SQLAlchemyError as e:
                log.exception(e)
                raise JobError(
                    "Connection with the database failed",
                ) from e

            try:
                model_metrics = {
                    split: {
                        metric.__name__: metric.score(
                            y[split],
                            model.predict(x[split]),
                        )
                        for metric in metrics
                    }
                    for split in ["train", "validation", "test"]
                }
            except Exception as e:
                log.exception(e)
                raise JobError(
                    "Metrics calculation failed",
                ) from e

            run.train_metrics = model_metrics["train"]
            run.validation_metrics = model_metrics["validation"]
            run.test_metrics = model_metrics["test"]

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
        except Exception as e:
            run.set_status_as_error()
            db.commit()
            raise e
