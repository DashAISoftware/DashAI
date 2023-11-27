import logging
import os
from typing import List

from sqlalchemy import exc
from sqlalchemy.orm import Session

from DashAI.back.api.api_v1.endpoints.components import _intersect_component_lists
from DashAI.back.core.config import component_registry, settings
from DashAI.back.database.models import Dataset, Experiment, Run
from DashAI.back.dataloaders.classes.dashai_dataset import (
    DashAIDataset,
    divide_by_columns,
    load_dataset,
)
from DashAI.back.metrics import BaseMetric
from DashAI.back.models import BaseModel
from DashAI.back.tasks import BaseTask

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)


class RunnerError(Exception):
    """Exception raised when the runner proccess fails."""


def execute_run(run_id: int, db: Session):
    """Function to train and evaluate a Run.
    It retrieves all the objects associated with the run and then it:
    - Trains the model.
    - Evaluate the model.
    - Save the trained model.

    Parameters
    ----------
    run_id: int
        id of the run to execute.

    Raises
    ----------
    RunnerError
        If an entity does not exist in the DB.
    RunnerError
        If the dataset does not exist in its path.
    RunnerError
        If unable to find a component in ComponentRegistry.
    RunnerError
        If the preparation of the dataset fails.
    RunnerError
        If the connection with the database fails.
    RunnerError
        If the training of the model fails.
    RunnerError
        If the evaluation of the model fails.
    RunnerError
        If the saving of the model fails.

    """
    run: Run = db.get(Run, run_id)
    if not run:
        raise RunnerError(f"Run {run_id} does not exist in DB.")
    try:
        experiment: Experiment = db.get(Experiment, run.experiment_id)
        if not experiment:
            raise RunnerError(f"Experiment {run.experiment_id} does not exist in DB.")
        dataset: Dataset = db.get(Dataset, experiment.dataset_id)
        if not dataset:
            raise RunnerError(f"Dataset {experiment.dataset_id} does not exist in DB.")

        try:
            loaded_dataset: DashAIDataset = load_dataset(f"{dataset.file_path}/dataset")
        except Exception as e:
            log.exception(e)
            raise RunnerError(
                f"Can not load dataset from path {dataset.file_path}",
            ) from e

        try:
            run_model_class = component_registry[run.model_name]["class"]
        except Exception as e:
            log.exception(e)
            raise RunnerError(
                f"Unable to find Model with name {run.model_name} in registry.",
            ) from e

        try:
            model: BaseModel = run_model_class(**run.parameters)
        except Exception as e:
            log.exception(e)
            raise RunnerError(
                f"Unable to instantiate model using run {run_id}",
            ) from e

        try:
            task: BaseTask = component_registry[experiment.task_name]["class"]()
        except Exception as e:
            log.exception(e)
            raise RunnerError(
                f"Unable to find Task with name {experiment.task_name} in registry",
            ) from e

        try:
            selected_metrics = {
                component_dict["name"]: component_dict
                for component_dict in component_registry.get_components_by_types(
                    select="Metric"
                )
            }
            selected_metrics = _intersect_component_lists(
                selected_metrics,
                component_registry.get_related_components(experiment.task_name),
            )
            metrics: List[BaseMetric] = [
                metric["class"] for metric in selected_metrics.values()
            ]
        except Exception as e:
            log.exception(e)
            raise RunnerError(
                "Unable to find metrics associated with"
                f"Task {experiment.task_name} in registry",
            ) from e

        try:
            prepared_dataset = task.prepare_for_task(
                loaded_dataset, experiment.output_columns
            )
            divided_dataset = divide_by_columns(
                prepared_dataset,
                experiment.input_columns,
                experiment.output_columns,
            )
        except Exception as e:
            log.exception(e)
            raise RunnerError(
                f"Can not prepare Dataset {dataset.id} for Task {experiment.task_name}",
            ) from e

        try:
            run.set_status_as_started()
            db.commit()
        except exc.SQLAlchemyError as e:
            log.exception(e)
            raise RunnerError(
                "Connection with the database failed",
            ) from e

        try:
            # Training
            model.fit(divided_dataset["train"][0], divided_dataset["train"][1])
        except Exception as e:
            log.exception(e)
            raise RunnerError(
                "Model training failed",
            ) from e

        try:
            run.set_status_as_finished()
            db.commit()
        except exc.SQLAlchemyError as e:
            log.exception(e)
            raise RunnerError(
                "Connection with the database failed",
            ) from e

        try:
            model_metrics = {
                split: {
                    metric.__name__: metric.score(
                        prepared_dataset[split],
                        model.predict(divided_dataset[split][0]),
                    )
                    for metric in metrics
                }
                for split in ["train", "validation", "test"]
            }
        except Exception as e:
            log.exception(e)
            raise RunnerError(
                "Metrics calculation failed",
            ) from e

        run.train_metrics = model_metrics["train"]
        run.validation_metrics = model_metrics["validation"]
        run.test_metrics = model_metrics["test"]

        try:
            os.makedirs(settings.USER_RUN_PATH, exist_ok=True)
            run_path = os.path.join(settings.USER_RUN_PATH, str(run.id))
            model.save(run_path)
        except Exception as e:
            log.exception(e)
            raise RunnerError(
                "Model saving failed",
            ) from e

        try:
            run.run_path = run_path
            db.commit()
        except exc.SQLAlchemyError as e:
            log.exception(e)
            run.set_status_as_error()
            db.commit()
            raise RunnerError(
                "Connection with the database failed",
            ) from e
    except Exception as e:
        run.set_status_as_error()
        db.commit()
        raise e
