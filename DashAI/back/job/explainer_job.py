import logging
import os

from dependency_injector.wiring import Provide, inject
from sqlalchemy import exc
from sqlalchemy.orm import Session

from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset, load_dataset
from DashAI.back.dependencies.database.models import (
    Dataset,
    Experiment,
    GlobalExplainer,
    LocalExplainer,
    Run,
)
from DashAI.back.explainability.global_explainer import BaseGlobalExplainer
from DashAI.back.explainability.local_explainer import BaseLocalExplainer
from DashAI.back.job.base_job import BaseJob, JobError
from DashAI.back.models import BaseModel
from DashAI.back.tasks import BaseTask

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)


class ExplainerJob(BaseJob):
    """ExplainerJob class to calculate explanations."""

    def set_status_as_delivered(self) -> None:
        """Set the status of the job as delivered."""
        explainer_id: int = self.kwargs["explainer_id"]
        db: Session = self.kwargs["db"]
        explainer_scope: str = self.kwargs["explainer_scope"]

        if explainer_scope == "global":
            explainer: GlobalExplainer = db.get(GlobalExplainer, explainer_id)
        elif explainer_scope == "local":
            explainer: LocalExplainer = db.get(LocalExplainer, explainer_id)
        else:
            raise JobError(f"{explainer_scope} is an invalid explainer type")

        if not explainer:
            raise JobError(f"Explainer {explainer_id} does not exist in DB.")
        try:
            explainer.set_status_as_delivered()
            db.commit()
        except exc.SQLAlchemyError as e:
            log.exception(e)
            raise JobError(
                "Internal database error",
            ) from e

    @inject
    def _generate_global_explanation(
        self,
        explainer_db: dict,
        explainer: BaseGlobalExplainer,
        dataset: DashAIDataset,
        config=Provide["config"],
    ):
        explainer_id: int = self.kwargs["explainer_id"]
        db: Session = self.kwargs["db"]

        try:
            explainer.explain(dataset)
        except Exception as e:
            log.exception(e)
            raise JobError(
                "Failed to generate the explanation",
            ) from e
        try:
            filename = f"global_explanation_{explainer_id}.json"
            explanation_path = os.path.join(config["EXPLANATIONS_PATH"], filename)
            explainer.save_explanation(explanation_path)
        except Exception as e:
            log.exception(e)
            raise JobError(
                "Explanation file saving failed",
            ) from e
        try:
            explainer_db.explanation_path = explanation_path
            db.commit()
        except Exception as e:
            log.exception(e)
            raise JobError(
                "Explanation path saving failed",
            ) from e

    @inject
    def _generate_local_explanation(
        self,
        explainer_db: dict,
        explainer: BaseLocalExplainer,
        dataset: DashAIDataset,
        task: BaseTask,
        config=Provide["config"],
    ):
        explainer_id: int = self.kwargs["explainer_id"]
        db: Session = self.kwargs["db"]

        explainer.fit(dataset, **explainer_db.fit_parameters)

        instance_id = explainer_db.dataset_id
        instance: Dataset = db.get(Dataset, instance_id)
        if not instance:
            raise JobError(
                f"Dataset {instance_id} to be explained does not exist in DB."
            )
        try:
            loaded_instance: DashAIDataset = load_dataset(
                f"{instance.file_path}/dataset"
            )
        except Exception as e:
            log.exception(e)
            raise JobError(
                f"Can not load instance from path {instance.file_path}",
            ) from e
        try:
            prepared_instance = task.prepare_for_task(loaded_instance)
        except Exception as e:
            log.exception(e)
            raise JobError(
                f"""Can not prepare Dataset with {instance_id}
                    to generate the local explanation.""",
            ) from e
        try:
            print(f"type instance: {prepared_instance.__class__}")
            explainer.explain_instance(prepared_instance)
        except Exception as e:
            log.exception(e)
            raise JobError(
                "Failed to generate the explanation",
            ) from e
        try:
            filename = f"local_explanation_{explainer_id}.json"
            explanation_path = os.path.join(config["EXPLANATIONS_PATH"], filename)
            explainer.save_explanation(explanation_path)
        except Exception as e:
            log.exception(e)
            raise JobError(
                "Explanation file saving failed",
            ) from e
        try:
            explainer_db.explanation_path = explanation_path
            db.commit()
        except Exception as e:
            log.exception(e)
            raise JobError(
                "Explanation path saving failed",
            ) from e

    @inject
    def run(
        self,
        component_registry=Provide["component_registry"],
    ) -> None:

        explainer_id: int = self.kwargs["explainer_id"]
        db: Session = self.kwargs["db"]
        explainer_scope: str = self.kwargs["explainer_scope"]

        if explainer_scope == "global":
            explainer_db: GlobalExplainer = db.get(GlobalExplainer, explainer_id)
        elif explainer_scope == "local":
            explainer_db: LocalExplainer = db.get(LocalExplainer, explainer_id)
        else:
            raise JobError(f"{explainer_scope} is an invalid explainer type")

        try:
            run: Run = db.get(Run, explainer_db.run_id)
            if not run:
                raise JobError(f"Run {explainer_db.run_id} does not exist in DB.")
            experiment: Experiment = db.get(Experiment, run.experiment_id)
            if not experiment:
                raise JobError(f"Experiment {run.experiment_id} does not exist in DB.")
            dataset: Dataset = db.get(Dataset, experiment.dataset_id)
            if not dataset:
                raise JobError(
                    f"Dataset {explainer_db.dataset_id} does not exist in DB."
                )

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
                raise JobError("Unable to instantiate model")
            try:
                trained_model = model.load(run.run_path)
            except Exception as e:
                log.exception(e)
                raise JobError(f"Can not load model from path {run.run_path}")
            try:
                explainer_class = component_registry[explainer_db.explainer_name][
                    "class"
                ]
            except Exception as e:
                log.exception(e)
                raise JobError(
                    f"""Unable to find the {explainer_scope} explainer with name
                        {explainer_db.explainer_name} in registry.""",
                ) from e

            try:
                explainer = explainer_class(
                    model=trained_model, **explainer_db.parameters
                )
            except Exception as e:
                log.exception(e)
                raise JobError(
                    f"Unable to instantiate {explainer_scope} explainer.",
                ) from e
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
                prepared_dataset = task.prepare_for_task(loaded_dataset)
            except Exception as e:
                log.exception(e)
                raise JobError(
                    f"""Can not prepare Dataset {dataset.id}
                    for Task {experiment.task_name}""",
                ) from e
            try:
                explainer_db.set_status_as_started()
                db.commit()
            except exc.SQLAlchemyError as e:
                log.exception(e)
                raise JobError(
                    "Connection with the database failed",
                ) from e

            if explainer_scope == "global":
                self._generate_global_explanation(
                    explainer_db=explainer_db,
                    explainer=explainer,
                    dataset=prepared_dataset,
                )

            elif explainer_scope == "local":
                self._generate_local_explanation(
                    explainer_db=explainer_db,
                    explainer=explainer,
                    dataset=prepared_dataset,
                    task=task,
                )
            else:
                raise JobError(f"{explainer_scope} is an invalid explainer type")

            explainer_db.set_status_as_finished()
            db.commit()

        except Exception as e:
            explainer_db.set_status_as_error()
            db.commit()
            raise e
