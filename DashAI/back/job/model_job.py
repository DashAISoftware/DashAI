import logging
import os
from typing import List

from sqlalchemy import exc
from sqlalchemy.orm import Session

from DashAI.back.database.models import Dataset, Experiment, Run
from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset, load_dataset
from DashAI.back.job.base_job import BaseJob, JobError
from DashAI.back.metrics import BaseMetric
from DashAI.back.models import BaseModel
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

    def run(self) -> None:
        from DashAI.back.api.api_v1.endpoints.components import (
            _intersect_component_lists,
        )
        from DashAI.back.core.config import component_registry, settings

        run_id: int = self.kwargs["run_id"]
        db: Session = self.kwargs["db"]

        run: Run = db.get(Run, run_id)
        try:
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
                run_model_class = component_registry[run.model_name]["class"]
            except Exception as e:
                log.exception(e)
                raise JobError(
                    f"Unable to find Model with name {run.model_name} in registry.",
                ) from e

            try:
                model: BaseModel = run_model_class(**run.parameters)
            except Exception as e:
                log.exception(e)
                raise JobError(
                    f"Unable to instantiate model using run {run_id}",
                ) from e

            try:
                task: BaseTask = component_registry[experiment.task_name]["class"]()
            except Exception as e:
                log.exception(e)
                raise JobError(
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
                raise JobError(
                    "Unable to find metrics associated with"
                    f"Task {experiment.task_name} in registry",
                ) from e

            try:
                prepared_dataset = task.prepare_for_task(loaded_dataset)
            except Exception as e:
                log.exception(e)
                raise JobError(
                    f"""Can not prepare Dataset {dataset.id}
                    for Task {experiment.task_name}""",
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
                # Training
                model.fit(prepared_dataset["train"])
            except Exception as e:
                log.exception(e)
                raise JobError(
                    "Model training failed",
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
                            prepared_dataset[split],
                            model.predict(prepared_dataset[split]),
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
                os.makedirs(settings.USER_RUN_PATH, exist_ok=True)
                run_path = os.path.join(settings.USER_RUN_PATH, str(run.id))
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