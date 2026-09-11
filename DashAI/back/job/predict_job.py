import logging
from typing import TYPE_CHECKING, Any, Dict, List, Tuple

from fastapi import status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import HTTPException
from kink import di, inject
from sqlalchemy import exc

from DashAI.back.dependencies.database.models import Dataset, ModelSession, Prediction
from DashAI.back.job.base_job import BaseJob, JobError
from DashAI.back.units.build_manual_input_unit import BuildManualInputUnit
from DashAI.back.units.context import ExecutionContext
from DashAI.back.units.load_dataset_unit import LoadDatasetUnit
from DashAI.back.units.load_trained_model_unit import LoadTrainedModelUnit
from DashAI.back.units.load_training_dataset_unit import LoadTrainingDatasetUnit
from DashAI.back.units.predict_unit import PredictUnit
from DashAI.back.units.save_prediction_unit import SavePredictionUnit

if TYPE_CHECKING:
    from sqlalchemy.orm import sessionmaker

    from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)


def _build_preview_rows(
    prepared_dataset: "DashAIDataset",
    input_columns: List[str],
    output_col: str,
    y_pred: Any,
) -> Tuple[List[str], List[List]]:
    """Build JSON-safe tabular rows for manual preview responses."""
    import base64

    columns = list(input_columns) + [output_col]

    def _to_native(v: Any) -> Any:
        return v.item() if hasattr(v, "item") else v

    rows: List[List] = []
    input_data = prepared_dataset.to_dict()
    for i in range(len(y_pred)):
        row = []
        for col in input_columns:
            val = input_data[col][i]
            if isinstance(val, bytes):
                val = "data:image/png;base64," + base64.b64encode(val).decode()
            elif isinstance(val, dict) and "bytes" in val:
                val = "data:image/png;base64," + base64.b64encode(val["bytes"]).decode()
            else:
                val = _to_native(val)
            row.append(val)
        row.append(_to_native(y_pred[i]))
        rows.append(row)

    columns_json = jsonable_encoder(columns)
    rows_json = jsonable_encoder(rows)
    return columns_json, rows_json


def run_manual_prediction(
    run_id: int,
    manual_input_data: List[Dict],
    session_factory: "sessionmaker",
) -> Tuple[List[str], List[List]]:
    """Execute a manual prediction synchronously without persisting results.

    Composes the same units ``PredictJob`` does, so there is one definition of
    what predicting means. The difference is entirely in the orchestration: no
    state row to advance, nothing written to disk, and failures reported as
    ``HTTPException`` because this runs inside a request instead of a worker.

    Each unit call sits in its own ``try`` so the HTTP response is decided by
    *which step* failed, never by matching on an error message. That is what
    keeps the endpoint's contract — eleven distinct responses across four status
    codes — independent of how the units happen to word their errors.

    Parameters
    ----------
    run_id : int
        The ID of the trained run.
    manual_input_data : List[Dict]
        List of row dicts keyed by input column name.
    session_factory : sessionmaker
        SQLAlchemy session factory, used for this function's own row reads. It
        must be the container's: the units resolve ``session_factory`` and
        ``component_registry`` from the DI container themselves, so a different
        one passed here would leave the two halves reading different databases.

    Returns
    -------
    Tuple[List[str], List[List]]
        A tuple of (columns, rows) where columns is the ordered list of
        column names (inputs + output) and rows is a list of value lists.

    Raises
    ------
    HTTPException
        On missing run, model session, or prediction failure.
    """
    from DashAI.back.dependencies.database.models import Run

    # Read everything this function needs off the rows, then let the session go:
    # nothing here writes, and the units open their own sessions.
    with session_factory() as db:
        run = db.get(Run, run_id)
        if not run:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Run not found for id {run_id}",
            )

        model_session: ModelSession = db.get(ModelSession, run.model_session_id)
        if not model_session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Model session not found",
            )

        dataset_trained: Dataset = db.get(Dataset, model_session.dataset_id)
        if not dataset_trained:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Training dataset not found",
            )

        if not model_session.input_columns:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Model session has no input columns configured",
            )

        if not model_session.output_columns:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Model session has no output columns configured",
            )

        task_name = model_session.task_name
        input_columns = list(model_session.input_columns)
        output_columns = list(model_session.output_columns)
        train_dataset_file_path = dataset_trained.file_path

    ctx = ExecutionContext()

    build_input = BuildManualInputUnit(
        task_name=task_name,
        train_dataset_file_path=train_dataset_file_path,
        manual_input_data=manual_input_data,
    )
    predict = PredictUnit(
        task_name=task_name,
        input_columns=input_columns,
        output_columns=output_columns,
    )

    try:
        # Both units resolve the task; validating up front keeps a missing task
        # reported as a task problem, ahead of the model, the way it always was.
        try:
            build_input.validate(ctx)
            predict.validate(ctx)
        except JobError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Task {task_name} not found in the registry",
            ) from e

        try:
            LoadTrainedModelUnit(run_id=run_id)(ctx)
        except JobError as e:
            # The unit distinguishes "not in the registry" from "cannot be read
            # from disk" with the same two texts this endpoint has always
            # returned, so its message is forwarded rather than rebuilt.
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e),
            ) from e

        try:
            LoadTrainingDatasetUnit(train_dataset_file_path=train_dataset_file_path)(
                ctx
            )
        except JobError as e:
            # Not forwarded: the unit names the path, this endpoint never has.
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Cannot load training dataset",
            ) from e

        try:
            build_input(ctx)
            predict(ctx)
            # Re-derived here rather than published by the unit: a narrowed view
            # of the dataset is exactly the kind of derived value that must not
            # cross a unit boundary, since anything upstream may reshape it.
            prepared_dataset = ctx.require("dataset").select_columns(input_columns)
        except (ValueError, TypeError) as e:
            logging.exception("Manual prediction input error: %s", e)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid input data: {str(e)}",
            ) from e
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Model prediction failed",
            ) from e

        return _build_preview_rows(
            prepared_dataset=prepared_dataset,
            input_columns=input_columns,
            output_col=output_columns[0],
            y_pred=ctx.require("y_pred"),
        )
    finally:
        ctx.clear_cache()


class PredictJob(BaseJob):
    """PredictJob class to run the prediction."""

    @inject
    def set_status_as_delivered(
        self, session_factory: "sessionmaker" = lambda di: di["session_factory"]
    ) -> None:
        """Set the status of the job as delivered."""
        prediction_id = self.kwargs.get("prediction_id")

        try:
            with session_factory() as db:
                prediction: Prediction = db.get(Prediction, prediction_id)
                if prediction:
                    prediction.set_status_as_delivered()
                    db.commit()
                else:
                    log.error(f"Prediction with id {prediction_id} not found.")
        except exc.SQLAlchemyError as e:
            log.exception(f"Database error while setting prediction status: {e}")

    @inject
    def set_status_as_error(
        self, session_factory: "sessionmaker" = lambda di: di["session_factory"]
    ) -> None:
        """Set the status of the prediction job as error."""
        prediction_id = self.kwargs.get("prediction_id")

        try:
            with session_factory() as db:
                prediction: Prediction = db.get(Prediction, prediction_id)
                if prediction:
                    prediction.set_status_as_error()
                    db.commit()
                else:
                    log.error(f"Prediction with id {prediction_id} not found.")
        except exc.SQLAlchemyError as e:
            log.exception(f"Database error while setting prediction status: {e}")

    @inject
    def get_job_name(self) -> str:
        """Get a descriptive name for the job."""
        prediction_id = self.kwargs.get("prediction_id")
        dataset_id = self.kwargs.get("dataset_id")

        if prediction_id:
            session_factory = di["session_factory"]

            try:
                with session_factory() as db:
                    prediction = db.get(Prediction, prediction_id)
                    dataset = db.get(Dataset, dataset_id)
                    if prediction and dataset:
                        return f"Predict: {prediction.run.name} on {dataset.name}"
            except Exception:
                pass

        return f"Prediction (Prediction:{prediction_id}, Dataset:{dataset_id})"

    @inject
    def run(
        self,
    ) -> List[Any]:
        session_factory = di["session_factory"]

        ctx = ExecutionContext()

        prediction_id: int = self.kwargs["prediction_id"]
        manual_input_data: List[dict] = self.kwargs.get("manual_input_data", [])

        with session_factory() as db:
            try:
                # Retrieve Prediction
                prediction: Prediction = db.get(Prediction, prediction_id)
                if not prediction:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Prediction not found for id {prediction_id}",
                    )

                # Set huey_id and update status to STARTED
                prediction.huey_id = self.kwargs.get("huey_id", None)
                prediction.set_status_as_started()
                db.commit()

                self.report_progress(0.1, "Loading model")

                dataset_id = prediction.dataset_id

                # Validate input data
                if not manual_input_data and not dataset_id:
                    prediction.set_status_as_error()
                    db.commit()
                    raise JobError(
                        "Either dataset_id or manual_input_data must be provided."
                    )

                # Retrieve Model Session
                model_session: ModelSession = db.get(
                    ModelSession, prediction.run.model_session_id
                )
                if not model_session:
                    prediction.set_status_as_error()
                    db.commit()
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Model session not found",
                    )

                # The dataset the model was trained on. The one to predict on,
                # when there is one, is resolved by the unit that loads it.
                dataset_trained: Dataset = db.get(Dataset, model_session.dataset_id)
                if not dataset_trained:
                    prediction.set_status_as_error()
                    db.commit()
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Training dataset not found",
                    )

                if not model_session.input_columns:
                    prediction.set_status_as_error()
                    db.commit()
                    raise HTTPException(
                        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                        detail="Model session has no input columns configured",
                    )

                if not model_session.output_columns:
                    prediction.set_status_as_error()
                    db.commit()
                    raise HTTPException(
                        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                        detail="Model session has no output columns configured",
                    )

            except exc.SQLAlchemyError as e:
                log.exception(e)
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Internal database error",
                ) from e

            # The prediction step owns the task, and resolving it here — before
            # the model is even looked up — is what keeps a missing task
            # reported as a task problem instead of being overtaken by
            # whatever fails next. Same shape as ModelJob validating the fit
            # unit ahead of the status change.
            predict = PredictUnit(
                task_name=model_session.task_name,
                input_columns=model_session.input_columns,
                output_columns=model_session.output_columns,
            )
            try:
                predict.validate(ctx)
            except Exception as e:
                prediction.set_status_as_error()
                db.commit()
                log.exception(e)
                raise

            # Load Model. The unit reports both the registry miss and the
            # unreadable artifact with the same texts the job used to build
            # here; re-raised as-is so they reach the user intact.
            try:
                LoadTrainedModelUnit(run_id=prediction.run_id)(ctx)
            except Exception as e:
                prediction.set_status_as_error()
                db.commit()
                log.exception(e)
                raise

            # Load training dataset for type info and label processing. Loaded
            # before the dataset to predict on, which is the order the error
            # messages depend on when both are unreadable.
            try:
                LoadTrainingDatasetUnit(
                    train_dataset_file_path=dataset_trained.file_path
                )(ctx)
            except Exception as e:
                # This branch used to skip set_status_as_error, unlike every
                # one around it, leaving the prediction STARTED forever.
                # Re-raised as-is so the unit's specific message survives.
                prediction.set_status_as_error()
                db.commit()
                log.exception(e)
                raise

            try:
                # Load or create prediction dataset. Both branches publish the
                # same "dataset" key, so the prediction below cannot tell a
                # dataset read from disk from one typed in by hand.
                if dataset_id:
                    LoadDatasetUnit(dataset_id=dataset_id)(ctx)
                else:
                    BuildManualInputUnit(
                        task_name=model_session.task_name,
                        train_dataset_file_path=dataset_trained.file_path,
                        manual_input_data=manual_input_data,
                    )(ctx)

                self.report_progress(0.4, "Running prediction")
                predict(ctx)

            except ValueError as ve:
                prediction.set_status_as_error()
                db.commit()
                log.error(f"Validation Error: {ve}")
                # JobError, not HTTPException: this runs in the Huey worker
                # and its exception travels back through dill. HTTPException
                # stores nothing in ``args``, so unpickling calls it with no
                # status code and the model's own complaint is replaced by a
                # deserialisation failure.
                raise JobError(f"Invalid input data: {ve}") from ve
            except TypeError as te:
                # Marked as failed like its ValueError neighbour: this branch
                # used to return 400 without touching the row, which left the
                # prediction STARTED forever.
                prediction.set_status_as_error()
                db.commit()
                log.error(f"Type Error: {te}")
                raise JobError(f"Type validation failed: {te}") from te
            except Exception as e:
                prediction.set_status_as_error()
                db.commit()
                log.error(e)
                raise JobError(
                    "Model prediction failed",
                ) from e

            self.report_progress(0.9, "Saving predictions")

            # Save Predictions to Arrow file
            try:
                SavePredictionUnit(
                    input_columns=model_session.input_columns,
                    output_columns=model_session.output_columns,
                )(ctx)

                # Update Prediction record
                prediction.results_path = ctx.require("results_path")
                prediction.set_status_as_finished()
                db.commit()
            except Exception as e:
                prediction.set_status_as_error()
                db.commit()
                log.exception(e)
                raise JobError(
                    "Can not save prediction to json file",
                ) from e
            finally:
                ctx.clear_cache()
