import json
import logging
import os
import pickle
from typing import Tuple

from datasets import DatasetDict
from dependency_injector.wiring import Provide, inject
from sqlalchemy import exc
from sqlalchemy.orm import Session

from DashAI.back.dataloaders.classes.dashai_dataset import (
    load_dataset,
    select_columns,
    update_dataset_splits,
)
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
            raise JobError(f"Explainer with id {explainer_id} does not exist in DB.")
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
        explainer: BaseGlobalExplainer,
        dataset=Tuple[DatasetDict, DatasetDict],
        config=Provide["config"],
    ):
        explainer_id: int = self.kwargs["explainer_id"]
        db: Session = self.kwargs["db"]

        try:
            explanation = explainer.explain(dataset)
        except Exception as e:
            log.exception(e)
            raise JobError(
                "Failed to generate the explanation",
            ) from e
        try:
            filename = f"global_explanation_{explainer_id}.pickle"
            explanation_path = os.path.join(config["EXPLANATIONS_PATH"], filename)
            with open(explanation_path, "wb") as file:
                pickle.dump(explanation, file)
        except Exception as e:
            log.exception(e)
            raise JobError(
                "Explanation file saving failed",
            ) from e
        try:
            self.explainer_db.explanation_path = explanation_path
            db.commit()
        except Exception as e:
            log.exception(e)
            raise JobError(
                "Explanation path saving failed",
            ) from e

    @inject
    def _generate_local_explanation(
        self,
        explainer: BaseLocalExplainer,
        dataset: Tuple[DatasetDict, DatasetDict],
        task: BaseTask,
        config=Provide["config"],
    ):
        explainer_id: int = self.kwargs["explainer_id"]
        db: Session = self.kwargs["db"]

        explainer.fit(dataset, **self.explainer_db.fit_parameters)

        instance_id = self.explainer_db.dataset_id
        instance: Dataset = db.get(Dataset, instance_id)
        if not instance:
            raise JobError(
                f"Dataset {instance_id} to be explained does not exist in DB."
            )
        try:
            loaded_instance: DatasetDict = load_dataset(f"{instance.file_path}/dataset")
        except Exception as e:
            log.exception(e)
            raise JobError(
                f"Can not load instance from path {instance.file_path}",
            ) from e
        try:
            prepared_instance = task.prepare_for_task(
                loaded_instance, outputs_columns=self.output_columns
            )
            X, _ = select_columns(
                prepared_instance,
                self.input_columns,
                self.output_columns,
            )
        except Exception as e:
            log.exception(e)
            raise JobError(
                f"""Can not prepare Dataset with {instance_id}
                    to generate the local explanation.""",
            ) from e
        try:
            explanation = explainer.explain_instance(X)
        except Exception as e:
            log.exception(e)
            raise JobError(
                "Failed to generate the explanation",
            ) from e
        try:
            filename = f"local_explanation_{explainer_id}.json"
            explanation_path = os.path.join(config["EXPLANATIONS_PATH"], filename)
            with open(explanation_path, "wb") as file:
                pickle.dump(explanation, file)
        except Exception as e:
            log.exception(e)
            raise JobError(
                "Explanation file saving failed",
            ) from e
        try:
            self.explainer_db.explanation_path = explanation_path
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
            self.explainer_db: GlobalExplainer = db.get(GlobalExplainer, explainer_id)
        elif explainer_scope == "local":
            self.explainer_db: LocalExplainer = db.get(LocalExplainer, explainer_id)
        else:
            raise JobError(f"{explainer_scope} is an invalid explainer type")

        try:
            run: Run = db.get(Run, self.explainer_db.run_id)
            if not run:
                raise JobError(f"Run {self.explainer_db.run_id} does not exist in DB.")
            experiment: Experiment = db.get(Experiment, run.experiment_id)
            if not experiment:
                raise JobError(f"Experiment {run.experiment_id} does not exist in DB.")
            dataset: Dataset = db.get(Dataset, experiment.dataset_id)
            if not dataset:
                raise JobError(
                    f"Dataset {self.explainer_db.dataset_id} does not exist in DB."
                )

            self.input_columns = experiment.input_columns
            self.output_columns = experiment.output_columns

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
                raise JobError("Unable to instantiate model") from e
            try:
                trained_model = model.load(run.run_path)
            except Exception as e:
                log.exception(e)
                raise JobError(f"Can not load model from path {run.run_path}") from e
            try:
                explainer_class = component_registry[self.explainer_db.explainer_name][
                    "class"
                ]
            except Exception as e:
                log.exception(e)
                raise JobError(
                    f"""Unable to find the {explainer_scope} explainer with name
                        {self.explainer_db.explainer_name} in registry.""",
                ) from e

            try:
                explainer = explainer_class(
                    model=trained_model, **self.explainer_db.parameters
                )
            except Exception as e:
                log.exception(e)
                raise JobError(
                    f"Unable to instantiate {explainer_scope} explainer.",
                ) from e
            try:
                loaded_dataset: DatasetDict = load_dataset(
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
                splits = json.loads(experiment.splits)
                if splits["has_changed"]:
                    new_splits = {
                        "train": splits["train"],
                        "test": splits["test"],
                        "validation": splits["validation"],
                    }
                    loaded_dataset = update_dataset_splits(
                        loaded_dataset, new_splits, splits["is_random"]
                    )
                prepared_dataset = task.prepare_for_task(
                    datasetdict=loaded_dataset,
                    outputs_columns=self.output_columns,
                )
                data = select_columns(
                    prepared_dataset,
                    self.input_columns,
                    self.output_columns,
                )

            except Exception as e:
                log.exception(e)
                raise JobError(
                    f"""Can not prepare dataset {dataset.id} for the explanation""",
                ) from e
            try:
                self.explainer_db.set_status_as_started()
                db.commit()
            except exc.SQLAlchemyError as e:
                log.exception(e)
                raise JobError(
                    "Connection with the database failed",
                ) from e

            if explainer_scope == "global":
                self._generate_global_explanation(explainer=explainer, dataset=data)

            elif explainer_scope == "local":
                self._generate_local_explanation(
                    explainer=explainer,
                    dataset=data,
                    task=task,
                )
            else:
                raise JobError(f"{explainer_scope} is an invalid explainer type")

            self.explainer_db.set_status_as_finished()
            db.commit()

        except Exception as e:
            self.explainer_db.set_status_as_error()
            db.commit()
            raise e
