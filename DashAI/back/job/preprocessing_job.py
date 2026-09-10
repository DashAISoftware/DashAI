import json
import logging
import os
import pickle
from typing import TYPE_CHECKING

from kink import inject
from sqlalchemy import exc

from DashAI.back.core.atomic import atomic_directory
from DashAI.back.dependencies.database.models import Dataset, ModelSession
from DashAI.back.job.base_job import BaseJob, JobError
from DashAI.back.preprocessing.column_ref import (
    ConverterSequence,
    parse_column_refs,
    resolve_refs,
)
from DashAI.back.preprocessing.session_preprocessor import SessionPreprocessor
from DashAI.back.splitters.splits_payload import normalize_splits_payload

if TYPE_CHECKING:
    from sqlalchemy.orm import sessionmaker

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)


class PreprocessingJob(BaseJob):
    """Fits a session's ConverterSequence once, ahead of any model training.

    Fits per fold for Cross-Validation (plus a final fit on the full
    training pool) or once for Holdout, and persists each fitted
    SessionPreprocessor so ModelJob, predict_job and explainer_job can
    reuse it without ever re-fitting on new data.
    """

    @inject
    def set_status_as_delivered(
        self, session_factory: "sessionmaker" = lambda di: di["session_factory"]
    ) -> None:
        model_session_id = self.kwargs["model_session_id"]
        with session_factory() as db:
            model_session = db.get(ModelSession, model_session_id)
            if model_session is None:
                raise JobError(
                    f"Model session {model_session_id} does not exist in DB."
                )
            try:
                db.commit()
            except exc.SQLAlchemyError as e:
                log.exception(e)
                raise JobError("Error setting preprocessing status as delivered") from e

    @inject
    def set_status_as_error(
        self, session_factory: "sessionmaker" = lambda di: di["session_factory"]
    ) -> None:
        model_session_id = self.kwargs.get("model_session_id")
        if model_session_id is None:
            return
        with session_factory() as db:
            model_session = db.get(ModelSession, model_session_id)
            if model_session is None:
                return
            model_session.preprocessing_status = "failed"
            try:
                db.commit()
            except exc.SQLAlchemyError as e:
                log.exception(e)

    @inject
    def get_job_name(self) -> str:
        model_session_id = self.kwargs.get("model_session_id")
        return f"Preprocessing: session {model_session_id}"

    @inject
    def run(self) -> None:
        from kink import di

        from DashAI.back.dataloaders.classes.dashai_dataset import load_dataset

        session_factory = di["session_factory"]
        component_registry = di["component_registry"]
        config = di["config"]

        model_session_id = self.kwargs["model_session_id"]

        with session_factory() as db:
            model_session: ModelSession = db.get(ModelSession, model_session_id)
            if not model_session:
                raise JobError(
                    f"Model session {model_session_id} does not exist in DB."
                )

            try:
                model_session.preprocessing_status = "pending"
                db.commit()

                dataset = db.get(Dataset, model_session.dataset_id)
                if not dataset:
                    raise JobError(
                        f"Dataset {model_session.dataset_id} does not exist in DB."
                    )
                loaded_dataset = load_dataset(f"{dataset.file_path}/dataset")

                sequence = ConverterSequence.model_validate(
                    model_session.preprocessing or {"steps": []}
                )
                sequence.validate_scopes()
                input_refs = parse_column_refs(model_session.input_column_refs or [])

                self.report_progress(0.05, "Splitting dataset")
                splits_data = normalize_splits_payload(json.loads(model_session.splits))
                splitter_name = splits_data.get("splitter_name")
                splitter = component_registry[splitter_name]["class"](
                    splits_data=splits_data
                )

                y_for_split = loaded_dataset.select_columns(
                    model_session.output_columns
                )
                x, _, _ = splitter.split(loaded_dataset, y_for_split)

                is_cv = isinstance(x, list)
                x_folds = x if is_cv else [x]
                total_folds = len(x_folds) - 1 if is_cv else 0

                artifacts_dir = os.path.join(
                    str(config["PREPROCESSING_PATH"]), str(model_session.id)
                )

                final_transformed = None
                final_resolved = None
                with atomic_directory(artifacts_dir) as tmp_dir:
                    for i in range(total_folds):
                        self.report_progress(
                            0.1 + 0.7 * (i / max(total_folds, 1)),
                            f"Fitting preprocessing for fold {i + 1}/{total_folds}",
                        )
                        fold_preprocessor = SessionPreprocessor(
                            sequence, component_registry
                        )
                        fold_preprocessor.fit_transform(x_folds[i])
                        with open(os.path.join(tmp_dir, f"fold_{i}.pkl"), "wb") as f:
                            pickle.dump(fold_preprocessor, f)

                    self.report_progress(0.85, "Fitting final preprocessing")
                    final_preprocessor = SessionPreprocessor(
                        sequence, component_registry
                    )
                    final_transformed, final_resolved = (
                        final_preprocessor.fit_transform(x_folds[-1])
                    )
                    with open(os.path.join(tmp_dir, "final.pkl"), "wb") as f:
                        pickle.dump(final_preprocessor, f)

                resolved_input_columns = resolve_refs(
                    input_refs, final_resolved, final_preprocessor.resolved_slots
                )

                self.report_progress(0.95, "Validating against the task")
                task = component_registry[model_session.task_name]["class"]()
                task.prepare_for_task(
                    dataset=final_transformed["train"],
                    input_columns=resolved_input_columns,
                    output_columns=model_session.output_columns,
                )

                model_session.input_columns = resolved_input_columns
                model_session.preprocessing_artifacts_path = artifacts_dir
                model_session.preprocessing_status = "ready"
                model_session.preprocessing_error = None
                db.commit()
            except (TypeError, ValueError) as e:
                log.exception(e)
                model_session.preprocessing_status = "failed"
                model_session.preprocessing_error = str(e)
                db.commit()
                raise JobError(
                    f"Preprocessing produced columns invalid for the task: {e}"
                ) from e
            except Exception as e:
                log.exception(e)
                model_session.preprocessing_status = "failed"
                model_session.preprocessing_error = str(e)
                db.commit()
                raise JobError(
                    f"Error running preprocessing for session {model_session_id}: {e}"
                ) from e
