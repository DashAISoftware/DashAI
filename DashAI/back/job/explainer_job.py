import logging
from typing import TYPE_CHECKING, Any, Dict, List, Tuple, Union

from kink import inject
from sqlalchemy import exc

from DashAI.back.converters.execution import (
    load_fitted_converters,
    transform_for_prediction,
)
from DashAI.back.dependencies.database.models import (
    Dataset,
    GlobalExplainer,
    LocalExplainer,
    ModelSession,
    Run,
)
from DashAI.back.explainability.global_explainer import BaseGlobalExplainer
from DashAI.back.explainability.local_explainer import BaseLocalExplainer
from DashAI.back.job.base_job import BaseJob, JobError
from DashAI.back.job.session_preprocessing_job import get_real_input_output_columns
from DashAI.back.models.base_model import BaseModel
from DashAI.back.tasks.base_task import BaseTask

if TYPE_CHECKING:
    from datasets import DatasetDict
    from sqlalchemy.orm import sessionmaker

    from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)


def _reapply_session_converters(
    data: Union["DatasetDict", "DashAIDataset"],
    fitted_converters: List[Dict[str, Any]],
) -> Union["DatasetDict", "DashAIDataset"]:
    """Replay a session's fitted converters (transform only, never re-fit) on
    explainer input, so it matches the feature space the model was trained
    on — the same reasoning as `predict_job.py`'s `_run_prediction_pipeline`.
    Accepts either a single partition or a `DatasetDict` of them; a no-op
    when `fitted_converters` is empty (session has no converters).
    """
    from datasets import DatasetDict

    if not fitted_converters:
        return data
    if isinstance(data, DatasetDict):
        return DatasetDict(
            {
                split_name: transform_for_prediction(part, fitted_converters)
                for split_name, part in data.items()
            }
        )
    return transform_for_prediction(data, fitted_converters)


class ExplainerJob(BaseJob):
    """ExplainerJob class to calculate explanations."""

    @inject
    def set_status_as_delivered(
        self, session_factory: "sessionmaker" = lambda di: di["session_factory"]
    ) -> None:
        """Set the status of the job as delivered."""
        explainer_id: int = self.kwargs["explainer_id"]
        explainer_scope: str = self.kwargs["explainer_scope"]

        with session_factory() as db:
            if explainer_scope == "global":
                explainer: GlobalExplainer = db.get(GlobalExplainer, explainer_id)
            elif explainer_scope == "local":
                explainer: LocalExplainer = db.get(LocalExplainer, explainer_id)
            else:
                raise JobError(f"{explainer_scope} is an invalid explainer type")

            if not explainer:
                raise JobError(
                    f"Explainer with id {explainer_id} does not exist in DB."
                )
            try:
                explainer.set_status_as_delivered()
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
        """Set the status of the explainer as error."""
        explainer_id: int = self.kwargs.get("explainer_id")
        explainer_scope: str = self.kwargs.get("explainer_scope", "")

        if explainer_id is None:
            return

        with session_factory() as db:
            try:
                if explainer_scope == "global":
                    explainer = db.get(GlobalExplainer, explainer_id)
                elif explainer_scope == "local":
                    explainer = db.get(LocalExplainer, explainer_id)
                else:
                    return

                if explainer:
                    explainer.set_status_as_error()
                    db.commit()
            except exc.SQLAlchemyError as e:
                log.exception(e)

    @inject
    def get_job_name(self) -> str:
        """Get a descriptive name for the job."""
        explainer_id = self.kwargs.get("explainer_id")
        explainer_scope = self.kwargs.get("explainer_scope", "")

        if not explainer_id:
            return f"{explainer_scope.capitalize()} Explanation"

        from kink import di

        session_factory = di["session_factory"]

        try:
            with session_factory() as db:
                if explainer_scope == "global":
                    explainer = db.get(GlobalExplainer, explainer_id)
                elif explainer_scope == "local":
                    explainer = db.get(LocalExplainer, explainer_id)
                else:
                    return (
                        f"{explainer_scope.capitalize()} Explanation ({explainer_id})"
                    )

                if explainer and explainer.name:
                    return f"Explain: {explainer.name}"
                if explainer and explainer.explainer_name:
                    return f"Explain: {explainer.explainer_name.split('.')[-1]}"
        except Exception:
            pass

        return f"{explainer_scope.capitalize()} Explanation ({explainer_id})"

    @inject
    def _generate_global_explanation(
        self,
        explainer: BaseGlobalExplainer,
        dataset=Tuple["DatasetDict", "DatasetDict"],
    ) -> None:
        import os
        import pickle

        from kink import di

        from DashAI.back.core.artifacts import normalize_artifacts

        explainer_id: int = self.kwargs["explainer_id"]
        session_factory = di["session_factory"]
        config = di["config"]
        with session_factory() as db:
            try:
                explanation = explainer.explain(dataset)
                plot = normalize_artifacts(explainer.plot(explanation))
            except Exception as e:
                log.exception(e)
                raise JobError(
                    "Failed to generate the explanation",
                ) from e
            try:
                explanation_filename = f"global_explanation_{explainer_id}.pickle"
                explanation_path = os.path.join(
                    config["EXPLANATIONS_PATH"], explanation_filename
                )
                with open(explanation_path, "wb") as file:
                    pickle.dump(explanation, file)

                plot_filename = f"global_explanation_plot_{explainer_id}.pickle"
                plot_path = os.path.join(config["EXPLANATIONS_PATH"], plot_filename)
                with open(plot_path, "wb") as file:
                    pickle.dump(plot, file)

            except Exception as e:
                log.exception(e)
                raise JobError(
                    "Explanation file saving failed",
                ) from e
            try:
                self.explainer_db.explanation_path = explanation_path
                self.explainer_db.plot_path = plot_path
                self.explainer_db.plot_overrides = None
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
        dataset: Tuple["DatasetDict", "DatasetDict"],
        splits: Dict[str, Any],
        task: BaseTask,
        same_dataset: bool,
        fitted_converters: List[Dict[str, Any]] = None,
    ) -> None:
        import json
        import os
        import pickle

        from datasets import DatasetDict
        from kink import di

        from DashAI.back.core.artifacts import normalize_artifacts
        from DashAI.back.dataloaders.classes.dashai_dataset import (
            load_dataset,
            prepare_for_model_session,
            save_dataset,
            select_columns,
            split_dataset,
        )

        explainer_id: int = self.kwargs["explainer_id"]
        session_factory = di["session_factory"]
        config = di["config"]

        explainer.fit(dataset, **self.explainer_db.fit_parameters)
        instance_id = self.explainer_db.dataset_id
        with session_factory() as db:
            instance: Dataset = db.get(Dataset, instance_id)
            if not instance:
                raise JobError(
                    f"Dataset {instance_id} to be explained does not exist in DB."
                )
            try:
                loaded_instance = load_dataset(f"{instance.file_path}/dataset")
            except Exception as e:
                log.exception(e)
                raise JobError(
                    f"Can not load instance from path {instance.file_path}",
                ) from e
            try:
                # The data source is selected via scope["mode"]. It defaults to
                # "split" so explainers created before this field existed keep
                # their original split + percentage behavior.
                mode = self.explainer_db.scope.get("mode", "split")

                if mode == "manual":
                    # Build the instances from values the user typed in by hand,
                    # reusing the same conversion the manual prediction flow uses.
                    # The rows (and any image files rewritten by the job endpoint)
                    # travel in the job kwargs, not in scope.
                    manual_input_data = self.kwargs.get("manual_input_data") or []
                    if not manual_input_data:
                        raise JobError(
                            "No manual input data provided for the explanation"
                        )
                    prepared_instance = task.process_manual_input(
                        manual_input_data,
                        f"{instance.file_path}/dataset",
                    )
                    # Manual input carries only the input columns (no target,
                    # and — like predict_job.py's manual-prediction contract —
                    # always in the *raw* schema: `process_manual_input`
                    # validates every entered key against the raw dataset, so
                    # `prepared_instance` already has exactly those columns.
                    # Never `self.input_columns` here: a converter that only
                    # appends (BagOfWords, LabelEncoder) names its *output*
                    # there, which doesn't exist in raw manual input yet — the
                    # reapply below is what produces it.
                    X = prepared_instance
                else:
                    # Not `self.input_columns`: same reasoning as the manual
                    # branch above — a converter that only appends means those
                    # names don't exist in `loaded_instance`'s raw schema yet.
                    raw_input_columns = [
                        col
                        for col in loaded_instance.column_names
                        if col not in self.output_columns
                    ]
                    if fitted_converters:
                        # `raw_input_columns` includes whatever a converter
                        # reads from (e.g. free text for BagOfWords), which
                        # is never itself a valid task input type — only
                        # the converter's *output* (self.input_columns) is
                        # meant to satisfy that. Skip the task's type
                        # validation on this intermediate raw data (same
                        # reasoning as predict_job.py's
                        # `_run_prediction_pipeline`).
                        from DashAI.back.dataloaders.classes.dashai_dataset import (
                            to_dashai_dataset,
                        )

                        prepared_instance = to_dashai_dataset(loaded_instance)
                    else:
                        prepared_instance = task.prepare_for_task(
                            loaded_instance,
                            input_columns=raw_input_columns,
                            output_columns=self.output_columns,
                        )

                    if mode == "rows":
                        # Explain a set of rows the user marked in the table.
                        # Indexes are over the whole dataset (the split does not
                        # apply in this mode).
                        row_indexes = self.explainer_db.scope.get("row_indexes") or []
                        valid_indexes = [
                            i
                            for i in row_indexes
                            if isinstance(i, int)
                            and 0 <= i < prepared_instance.num_rows
                        ]
                        if row_indexes and not valid_indexes:
                            raise JobError(
                                "No valid row indexes provided for the explanation"
                            )
                        if valid_indexes:
                            prepared_instance = prepared_instance.select(valid_indexes)
                    else:
                        split = self.explainer_db.scope.get("split")
                        if split not in ["train", "test", "val", "all"]:
                            raise JobError(f"{split} is not a valid split")

                        if split != "all":
                            if not same_dataset:
                                if isinstance(splits, str):
                                    splits = json.loads(splits)
                                (
                                    prepared_dataset_dict,
                                    splits,
                                ) = prepare_for_model_session(
                                    dataset=prepared_instance,
                                    splits=splits,
                                    output_columns=self.output_columns,
                                )
                                split_key = "validation" if split == "val" else split
                                prepared_instance = prepared_dataset_dict[split_key]
                            else:
                                prepared_instance = split_dataset(
                                    prepared_instance,
                                    train_indexes=splits["train_indexes"],
                                    test_indexes=splits["test_indexes"],
                                    val_indexes=splits["val_indexes"],
                                )
                                split_key = "validation" if split == "val" else split
                                prepared_instance = prepared_instance[split_key]

                        n_rows = max(
                            1,
                            int(
                                prepared_instance.num_rows
                                * self.explainer_db.scope.get("percentage")
                                / 100
                            ),
                        )
                        # When "shuffle" is set the percentage is taken as a random
                        # sample of the split; otherwise it is the leading rows.
                        if self.explainer_db.scope.get("shuffle"):
                            prepared_instance = prepared_instance.shuffle(seed=42)
                        prepared_instance = prepared_instance.select(range(n_rows))

                    prepared_instance = DatasetDict({"train": prepared_instance})
                    X, _ = select_columns(
                        prepared_instance,
                        raw_input_columns,
                        self.output_columns,
                    )
                # Persist the original selected rows (the model input for each
                # explained instance) as a DashAIDataset before the model's own
                # preprocessing runs, so the frontend can read them back with
                # the existing dataset endpoints.
                input_source = X["train"] if isinstance(X, DatasetDict) else X
                input_dataset_path = os.path.join(
                    config["EXPLANATIONS_PATH"],
                    f"local_explanation_input_{explainer_id}",
                )
                save_dataset(input_source, os.path.join(input_dataset_path, "dataset"))
                # Session converters (if any) are replayed here — same
                # reasoning as predict_job.py: the model was trained on
                # transformed data, so explained instances must match that
                # feature space too. The model's own internal preprocessing
                # (prepare_model_input) is a separate, later step some
                # explainers apply on top of this.
                X = _reapply_session_converters(X, fitted_converters or [])
                # Narrow to exactly what the model was trained on — a
                # converter that only appends (BagOfWords, LabelEncoder)
                # leaves its original column sitting alongside the new
                # ones; the model never saw that column.
                if isinstance(X, DatasetDict):
                    X = DatasetDict(
                        {
                            split_name: part.select_columns(self.input_columns)
                            for split_name, part in X.items()
                        }
                    )
                else:
                    X = X.select_columns(self.input_columns)

            except Exception as e:
                log.exception(e)
                raise JobError(
                    f"""Can not prepare Dataset with {instance_id}
                        to generate the local explanation.""",
                ) from e
            try:
                explanation = explainer.explain_instance(X)
                plots = normalize_artifacts(
                    explainer.plot(explanation), create_grouped=True
                )
            except Exception as e:
                log.exception(e)
                raise JobError(
                    "Failed to generate the explanation",
                ) from e
            try:
                explanation_filename = f"local_explanation_{explainer_id}.pickle"
                explanation_path = os.path.join(
                    config["EXPLANATIONS_PATH"], explanation_filename
                )
                with open(explanation_path, "wb") as file:
                    pickle.dump(explanation, file)

                plots_filename = f"local_explanation_plots_{explainer_id}.pickle"
                plots_path = os.path.join(config["EXPLANATIONS_PATH"], plots_filename)
                with open(plots_path, "wb") as file:
                    pickle.dump(plots, file)

            except Exception as e:
                log.exception(e)
                raise JobError(
                    "Explanation file saving failed",
                ) from e
            try:
                self.explainer_db.explanation_path = explanation_path
                self.explainer_db.plots_path = plots_path
                self.explainer_db.input_dataset_path = input_dataset_path
                self.explainer_db.plot_overrides = None
                db.commit()
            except Exception as e:
                log.exception(e)
                raise JobError(
                    "Explanation path saving failed",
                ) from e

    @inject
    def run(
        self,
    ) -> None:
        import json

        from datasets import DatasetDict
        from kink import di

        from DashAI.back.dataloaders.classes.dashai_dataset import (
            load_dataset,
            select_columns,
            split_dataset,
        )

        component_registry = di["component_registry"]
        session_factory = di["session_factory"]

        explainer_id: int = self.kwargs["explainer_id"]
        explainer_scope: str = self.kwargs["explainer_scope"]
        with session_factory() as db:
            if explainer_scope == "global":
                self.explainer_db: GlobalExplainer = db.get(
                    GlobalExplainer, explainer_id
                )
            elif explainer_scope == "local":
                self.explainer_db: LocalExplainer = db.get(LocalExplainer, explainer_id)
            else:
                raise JobError(f"{explainer_scope} is an invalid explainer type")

            try:
                run: Run = db.get(Run, self.explainer_db.run_id)
                if not run:
                    raise JobError(
                        f"Run {self.explainer_db.run_id} does not exist in DB."
                    )
                model_session: ModelSession = db.get(ModelSession, run.model_session_id)
                if not model_session:
                    raise JobError(
                        f"Model session {run.model_session_id} does not exist in DB."
                    )
                dataset: Dataset = db.get(Dataset, model_session.dataset_id)
                if not dataset:
                    raise JobError(
                        f"Dataset {self.explainer_db.dataset_id} does not exist in DB."
                    )

                self.input_columns, self.output_columns = get_real_input_output_columns(
                    model_session
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
                    raise JobError("Unable to instantiate model") from e
                try:
                    trained_model = model.load(run.run_path)
                except Exception as e:
                    log.exception(e)
                    raise JobError(
                        f"Can not load model from path {run.run_path}"
                    ) from e
                try:
                    explainer_class = component_registry[
                        self.explainer_db.explainer_name
                    ]["class"]
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
                    loaded_dataset: "DatasetDict" = load_dataset(
                        f"{dataset.file_path}/dataset"
                    )
                except Exception as e:
                    log.exception(e)
                    raise JobError(
                        f"Can not load dataset from path {dataset.file_path}",
                    ) from e
                try:
                    task: BaseTask = component_registry[model_session.task_name][
                        "class"
                    ]()
                except Exception as e:
                    log.exception(e)
                    raise JobError(
                        (
                            f"Unable to find Task with name {model_session.task_name} "
                            "in registry"
                        ),
                    ) from e
                try:
                    splits = json.loads(run.split_indexes)
                    # `self.input_columns`/`self.output_columns` name the
                    # session's *final* columns — a converter that only
                    # appends (BagOfWords' `bow_<word>`, LabelEncoder's
                    # `le_<col>`) means those input names don't exist in the
                    # raw dataset yet. Validate/select the *raw* inputs
                    # (everything except output) first; the fitted
                    # converters replayed below reproduce
                    # `self.input_columns` from there — same reasoning as
                    # predict_job.py's `_run_prediction_pipeline`.
                    raw_input_columns = [
                        col
                        for col in loaded_dataset.column_names
                        if col not in self.output_columns
                    ]
                    loaded_dataset = split_dataset(
                        loaded_dataset,
                        train_indexes=splits["train_indexes"],
                        test_indexes=splits["test_indexes"],
                        val_indexes=splits["val_indexes"],
                    )

                    if model_session.converters:
                        # `raw_input_columns` includes whatever a converter
                        # reads from (e.g. free text for BagOfWords), which
                        # is never itself a valid task input type — only
                        # the converter's *output* (self.input_columns) is
                        # meant to satisfy that. Skip the task's type
                        # validation on this intermediate raw data; the
                        # column selection below is all it's needed for
                        # (same reasoning as predict_job.py's
                        # `_run_prediction_pipeline`, which never validates
                        # the raw stage either).
                        from DashAI.back.dataloaders.classes.dashai_dataset import (
                            to_dashai_dataset,
                        )

                        prepared_dataset = to_dashai_dataset(loaded_dataset)
                    else:
                        prepared_dataset = task.prepare_for_task(
                            dataset=loaded_dataset,
                            input_columns=raw_input_columns,
                            output_columns=self.output_columns,
                        )
                    data = select_columns(
                        prepared_dataset,
                        raw_input_columns,
                        self.output_columns,
                    )

                    data_x = split_dataset(
                        data[0],
                        train_indexes=splits["train_indexes"],
                        test_indexes=splits["test_indexes"],
                        val_indexes=splits["val_indexes"],
                    )
                    data_y = split_dataset(
                        data[1],
                        train_indexes=splits["train_indexes"],
                        test_indexes=splits["test_indexes"],
                        val_indexes=splits["val_indexes"],
                    )
                    # Inputs stay unprepared (see the note in the local
                    # explanation path); targets are encoded because explainers
                    # compare them against the model's class indexes.
                    for split_name in data_y:
                        data_y[split_name] = trained_model.prepare_output(
                            data_y[split_name], is_fit=False
                        )

                    # Replay session converters (if any) on the inputs, so
                    # this matches the feature space the model was actually
                    # trained on — same reasoning as predict_job.py.
                    fitted_converters = []
                    if model_session.converters and model_session.preprocessed_path:
                        fitted_converters = load_fitted_converters(
                            model_session.preprocessed_path
                        )
                    data_x = _reapply_session_converters(data_x, fitted_converters)
                    # Narrow to exactly what the model was trained on — a
                    # converter that only appends leaves its original column
                    # sitting alongside the new ones; the model never saw it.
                    data_x = DatasetDict(
                        {
                            split_name: part.select_columns(self.input_columns)
                            for split_name, part in data_x.items()
                        }
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
                    self._generate_global_explanation(
                        explainer=explainer, dataset=(data_x, data_y)
                    )

                elif explainer_scope == "local":
                    same_dataset = (
                        model_session.dataset_id == self.explainer_db.dataset_id
                    )
                    if not same_dataset:
                        splits = model_session.splits

                    self._generate_local_explanation(
                        explainer=explainer,
                        dataset=(data_x, data_y),
                        splits=splits,
                        task=task,
                        same_dataset=same_dataset,
                        fitted_converters=fitted_converters,
                    )
                else:
                    raise JobError(f"{explainer_scope} is an invalid explainer type")

                self.explainer_db.set_status_as_finished()
                db.commit()

            except Exception as e:
                self.explainer_db.set_status_as_error()
                db.commit()
                raise e
