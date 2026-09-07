import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Tuple

from fastapi import status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import HTTPException
from kink import di, inject
from sqlalchemy import exc

from DashAI.back.dependencies.database.models import Dataset, ModelSession, Prediction
from DashAI.back.job.base_job import BaseJob, JobError
from DashAI.back.models.base_model import BaseModel
from DashAI.back.splitters.splits_payload import run_split_indexes
from DashAI.back.tasks.base_task import BaseTask
from DashAI.back.tasks.regression_task import RegressionTask

if TYPE_CHECKING:
    from sqlalchemy.orm import sessionmaker

    from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)


def _run_prediction_pipeline(
    task: BaseTask,
    trained_model: BaseModel,
    train_dataset: "DashAIDataset",
    loaded_dataset: "DashAIDataset",
    model_session: ModelSession,
) -> Tuple["DashAIDataset", Any]:
    """Run shared prediction steps from prepared input data to final predictions.

    Parameters
    ----------
    task : BaseTask
        The task the run belongs to.
    trained_model : BaseModel
        The model loaded from the run.
    train_dataset : DashAIDataset
        The dataset the model was trained on, for type and label information.
    loaded_dataset : DashAIDataset
        The rows to predict.
    model_session : ModelSession
        The session declaring the input and output columns.

    Returns
    -------
    tuple
        The prepared inputs and the predictions for them.
    """
    import numpy as np

    prepared_dataset = loaded_dataset.select_columns(model_session.input_columns)
    y_pred_proba = np.array(trained_model.predict(prepared_dataset))
    y_pred = task.process_predictions(
        train_dataset, y_pred_proba, model_session.output_columns[0]
    )
    return prepared_dataset, y_pred


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
    component_registry: Any,
    session_factory: "sessionmaker",
) -> Tuple[List[str], List[List]]:
    """Execute a manual prediction synchronously without persisting results.

    Parameters
    ----------
    run_id : int
        The ID of the trained run.
    manual_input_data : List[Dict]
        List of row dicts keyed by input column name.
    component_registry : Any
        The DashAI component registry.
    session_factory : sessionmaker
        SQLAlchemy session factory.

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
    with session_factory() as db:
        from DashAI.back.dataloaders.classes.dashai_dataset import load_dataset
        from DashAI.back.dependencies.database.models import Run

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

        try:
            task: BaseTask = component_registry[model_session.task_name]["class"]()
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Task {model_session.task_name} not found in the registry",
            ) from e

        try:
            model_cls = component_registry[run.model_name]["class"]
        except KeyError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Model {run.model_name} not found in the registry",
            ) from e

        try:
            trained_model: BaseModel = model_cls.load(run.run_path)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=(
                    f"Failed to load model {run.model_name} from path {run.run_path}"
                ),
            ) from e

        try:
            train_dataset: "DashAIDataset" = load_dataset(
                str(Path(f"{dataset_trained.file_path}/dataset/"))
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Cannot load training dataset",
            ) from e

        try:
            dataset_trained_path = str(Path(f"{dataset_trained.file_path}/dataset/"))
            loaded_dataset: "DashAIDataset" = task.process_manual_input(
                manual_input_data, dataset_trained_path
            )
            prepared_dataset, y_pred = _run_prediction_pipeline(
                task=task,
                trained_model=trained_model,
                train_dataset=train_dataset,
                loaded_dataset=loaded_dataset,
                model_session=model_session,
            )
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

        output_col = model_session.output_columns[0]
        return _build_preview_rows(
            prepared_dataset=prepared_dataset,
            input_columns=list(model_session.input_columns),
            output_col=output_col,
            y_pred=y_pred,
        )


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
        import uuid
        from pathlib import Path

        from DashAI.back.dataloaders.classes.dashai_dataset import (
            load_dataset,
            save_dataset,
            to_dashai_dataset,
        )

        component_registry = di["component_registry"]
        session_factory = di["session_factory"]
        config = di["config"]

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

                # Retrieve Dataset if dataset_id is provided
                dataset: Dataset = None
                dataset_trained: Dataset = db.get(Dataset, model_session.dataset_id)
                if not dataset_trained:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Training dataset not found",
                    )

                if dataset_id:
                    dataset: Dataset = db.get(Dataset, dataset_id)

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

            # Retrieve Task
            try:
                task: BaseTask = component_registry[model_session.task_name]["class"]()
            except Exception as e:
                prediction.set_status_as_error()
                db.commit()
                log.exception(e)
                raise JobError(
                    f"Task {model_session.task_name} not found in the registry",
                ) from e

            # Load Model
            try:
                model = component_registry[prediction.run.model_name]["class"]
            except KeyError as e:
                prediction.set_status_as_error()
                db.commit()
                log.exception(e)
                raise JobError(
                    f"Model {prediction.run.model_name} not found in the registry"
                ) from e

            try:
                trained_model: BaseModel = model.load(prediction.run.run_path)
            except Exception as e:
                prediction.set_status_as_error()
                db.commit()
                log.exception(e)
                raise JobError(
                    f"Failed to load model {prediction.run.model_name} "
                    f"from path {prediction.run.run_path}"
                ) from e

            # Load Dataset and make Predictions
            try:
                # Load training dataset for type info and label processing
                train_dataset: "DashAIDataset" = load_dataset(
                    str(Path(f"{dataset_trained.file_path}/dataset/"))
                )
            except Exception as e:
                log.exception(e)
                raise JobError(
                    f"Cannot load training dataset from "
                    f"{dataset_trained.file_path}/dataset/"
                ) from e

            row_indexes = None
            if prediction.split and dataset_id == model_session.dataset_id:
                try:
                    row_indexes = run_split_indexes(
                        model_session.splits,
                        prediction.run.split_indexes,
                        component_registry,
                        prediction.split,
                    )
                except ValueError as e:
                    prediction.set_status_as_error()
                    db.commit()
                    log.exception(e)
                    raise JobError(
                        f"Cannot predict on the {prediction.split} split: {e}"
                    ) from e

            try:
                # Load or create prediction dataset
                if dataset_id:
                    loaded_dataset: "DashAIDataset" = load_dataset(
                        str(Path(f"{dataset.file_path}/dataset/"))
                    )
                    if row_indexes is not None:
                        loaded_dataset = loaded_dataset.select(row_indexes)
                else:
                    dataset_trained_path = str(
                        Path(f"{dataset_trained.file_path}/dataset/")
                    )
                    loaded_dataset = task.process_manual_input(
                        manual_input_data, dataset_trained_path
                    )

                self.report_progress(0.4, "Running prediction")
                _, y_pred = _run_prediction_pipeline(
                    task=task,
                    trained_model=trained_model,
                    train_dataset=train_dataset,
                    loaded_dataset=loaded_dataset,
                    model_session=model_session,
                )

            except ValueError as ve:
                prediction.set_status_as_error()
                db.commit()
                log.error(f"Validation Error: {ve}")
                raise JobError(f"Invalid input data: {ve}") from ve
            except TypeError as te:
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
                # Create unique folder for predictions
                path = str(Path(f"{config['DATASETS_PATH']}/predictions/"))
                folder_name = str(uuid.uuid4())
                full_path = Path(path) / folder_name
                full_path.mkdir(parents=True, exist_ok=True)

                output_col = model_session.output_columns[0]
                base_columns = [
                    col for col in loaded_dataset.column_names if col != output_col
                ]
                output_dataset = loaded_dataset.select_columns(base_columns)
                dataset_with_prediction = to_dashai_dataset(
                    output_dataset.add_column(output_col, y_pred)
                )

                # Filter schema from trained dataset
                trained_schema = train_dataset.types
                filtered_schema = {
                    key: value.to_string()
                    for key, value in trained_schema.items()
                    if key in model_session.input_columns + model_session.output_columns
                }

                # Regression models predict continuous values regardless of
                # the training target's original dtype (e.g. a target column
                # that happened to hold only integer-looking values), so the
                # output column's saved schema must reflect that instead of
                # inheriting the training dataset's type.
                if isinstance(task, RegressionTask):
                    filtered_schema[output_col] = {"type": "Float", "dtype": "float64"}

                # Store num of rows, columns, and column names
                dataset_with_prediction.compute_base_metadata()

                # Save dataset with predictions
                save_dataset(
                    dataset_with_prediction,
                    str(full_path / "dataset"),
                    filtered_schema,
                )

                # Update Prediction record
                prediction.results_path = str(full_path)
                prediction.set_status_as_finished()
                db.commit()
            except Exception as e:
                prediction.set_status_as_error()
                db.commit()
                log.exception(e)
                raise JobError(
                    "Can not save prediction to json file",
                ) from e
