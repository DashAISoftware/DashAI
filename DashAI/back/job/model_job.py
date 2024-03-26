import logging
import os
from multiprocessing.connection import PipeConnection
from typing import List, Type

from dependency_injector.wiring import Provide, inject
from sqlalchemy import exc

from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset, load_dataset
from DashAI.back.dependencies.database.models import Dataset, Experiment, Run
from DashAI.back.job.base_job import BaseJob, JobError
from DashAI.back.metrics import BaseMetric
from DashAI.back.models import BaseModel
from DashAI.back.tasks import BaseTask

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)


class ModelJob(BaseJob):
    """ModelJob class to run the model training."""

    @inject
    def get_args(
        self,
        component_registry=Provide["component_registry"],
        session_factory=Provide["db"],
    ) -> dict:
        from DashAI.back.api.api_v1.endpoints.components import (
            _intersect_component_lists,
        )

        with session_factory.session() as db:
            run: Run = db.get(Run, self.kwargs["run_id"])
            if not run:
                raise JobError(f"Run {self.kwargs['run_id']} does not exist in DB.")
            experiment: Experiment = db.get(Experiment, run.experiment_id)
            if not experiment:
                raise JobError(f"Experiment {run.experiment_id} does not exist in DB.")
            dataset: Dataset = db.get(Dataset, experiment.dataset_id)
            if not experiment:
                raise JobError(f"Dataset {experiment.dataset_id} does not exist in DB.")
            try:
                model_class = component_registry[run.model_name]["class"]
                task_class = component_registry[experiment.task_name]["class"]
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
            except (KeyError, ValueError) as e:
                log.exception(e)
                raise JobError(
                    f"Unable to find component classes for run {run.id}"
                ) from e
            metrics_classes = [metric["class"] for metric in selected_metrics.values()]
            return {
                "dataset_id": dataset.id,
                "dataset_file_path": dataset.file_path,
                "model_class": model_class,
                "model_kwargs": run.parameters,
                "task_class": task_class,
                "metrics_classes": metrics_classes,
            }

    @inject
    def run(
        self,
        dataset_id: int,
        dataset_file_path: str,
        model_class: Type[BaseModel],
        model_kwargs: dict,
        task_class: Type[BaseTask],
        metrics_classes: List[Type[BaseMetric]],
        pipe: PipeConnection,
    ) -> None:
        try:
            loaded_dataset: DashAIDataset = load_dataset(f"{dataset_file_path}/dataset")
        except Exception as e:
            log.exception(e)
            raise JobError(
                f"Can not load dataset from path {dataset_file_path}",
            ) from e

        try:
            model: BaseModel = model_class(**model_kwargs)
        except Exception as e:
            log.exception(e)
            raise JobError(
                f"Unable to instantiate model using run {self.kwargs['run_id']}",
            ) from e

        try:
            prepared_dataset = task_class().prepare_for_task(loaded_dataset)
        except Exception as e:
            log.exception(e)
            raise JobError(
                f"""Can not prepare Dataset {dataset_id}
                for Task {task_class.__name__}""",
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
            model_metrics = {
                split: {
                    metric.__name__: metric.score(
                        prepared_dataset[split],
                        model.predict(prepared_dataset[split]),
                    )
                    for metric in metrics_classes
                }
                for split in ["train", "validation", "test"]
            }
        except Exception as e:
            log.exception(e)
            raise JobError(
                "Metrics calculation failed",
            ) from e

        pipe.send(
            {
                "model": model,
                "metrics": model_metrics,
            }
        )

    @inject
    def store_results(
        self,
        model: BaseModel,
        metrics: dict,
        session_factory=Provide["db"],
        config=Provide["config"],
    ) -> None:
        with session_factory.session() as db:
            run: Run = db.get(Run, self.kwargs["run_id"])

            try:
                run_path = os.path.join(config["RUNS_PATH"], str(run.id))
                model.save(run_path)
            except Exception as e:
                log.exception(e)
                raise JobError(
                    "Model saving failed",
                ) from e

            run.train_metrics = metrics["train"]
            run.validation_metrics = metrics["validation"]
            run.test_metrics = metrics["test"]
            run.run_path = run_path
            try:
                db.commit()
            except exc.SQLAlchemyError as e:
                log.exception(e)
                run.set_status_as_error()
                db.commit()
                raise JobError(
                    "Connection with the database failed",
                ) from e
