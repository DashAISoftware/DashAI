import logging
from typing import TYPE_CHECKING, Union

from fastapi import APIRouter, Depends, Response, status
from fastapi.exceptions import HTTPException
from kink import di, inject
from pydantic import ValidationError
from sqlalchemy import exc, select

from DashAI.back.api.api_v1.schemas.model_sessions_params import (
    ColumnsValidationParams,
    ModelSessionBulkDeleteParams,
    ModelSessionParams,
)
from DashAI.back.api.utils import remove_path
from DashAI.back.dependencies.database.models import Dataset, ModelSession, Run
from DashAI.back.splitters.splits_payload import (
    META_KEYS,
    normalize_splits_payload,
    schema_placeholder_defaults,
)

if TYPE_CHECKING:
    from sqlalchemy.orm import sessionmaker

    from DashAI.back.dependencies.registry import ComponentRegistry
    from DashAI.back.tasks.base_task import BaseTask


logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)

router = APIRouter()


@router.get("/")
@inject
async def get_model_sessions(
    session_factory: "sessionmaker" = Depends(lambda: di["session_factory"]),
):
    """Retrieve a list of the stored model sessions in the database.

    Parameters
    ----------
    session_factory : Callable[..., ContextManager[Session]]
        A factory that creates a context manager that handles a SQLAlchemy session.
        The generated session can be used to access and query the database.


    Returns
    -------
    List[dict]
        A list of dict containing model sessions.
    """
    with session_factory() as db:
        try:
            all_model_sessions = db.query(ModelSession).all()
        except exc.SQLAlchemyError as e:
            log.exception(e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal database error",
            ) from e
        return all_model_sessions


@router.get("/{model_session_id}")
@inject
async def get_model_session(
    model_session_id: int,
    session_factory: "sessionmaker" = Depends(lambda: di["session_factory"]),
):
    """Retrieve the model session associated with the provided ID.

    Parameters
    ----------
    model_session_id : int
        ID of the model session to retrieve.
    session_factory : Callable[..., ContextManager[Session]]
        A factory that creates a context manager that handles a SQLAlchemy session.
        The generated session can be used to access and query the database.

    Returns
    -------
    JSON
        JSON with the specified model session id.
    """
    with session_factory() as db:
        try:
            model_session = db.get(ModelSession, model_session_id)
            if not model_session:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Model session not found",
                )
        except exc.SQLAlchemyError as e:
            log.exception(e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal database error",
            ) from e
        return model_session


@router.post("/validation")
@inject
async def validate_columns(
    params: ColumnsValidationParams,
    component_registry: "ComponentRegistry" = Depends(lambda: di["component_registry"]),
    session_factory: "sessionmaker" = Depends(lambda: di["session_factory"]),
):
    """Validate if dataset columns are compatible with a task."""
    import os

    import pyarrow as pa
    import pyarrow.ipc as ipc

    from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset

    with session_factory() as db:
        try:
            dataset = db.get(Dataset, params.dataset_id)
            if not dataset:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Dataset not found",
                )

            dataset_path = f"{dataset.file_path}/dataset"
            data_filepath = os.path.join(dataset_path, "data.arrow")
            with pa.OSFile(data_filepath, "rb") as source:
                reader = ipc.open_file(source)
                batch = reader.get_batch(0)
                sample_size = min(5, batch.num_rows)
                sample_batch = batch.slice(0, sample_size)

            table = pa.Table.from_batches([sample_batch])
            minimal_dataset = DashAIDataset(table)

            column_names = minimal_dataset.column_names

            if len(params.inputs_columns + params.outputs_columns) > len(column_names):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Column index out of range",
                )

            inputs_names = params.inputs_columns
            outputs_names = params.outputs_columns

        except exc.SQLAlchemyError as e:
            log.exception(e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal database error",
            ) from e

    if params.task_name not in component_registry:
        raise HTTPException(
            status_code=404,
            detail=f"Task {params.task_name} not found in the registry.",
        )

    task: "BaseTask" = component_registry[params.task_name]["class"]()
    validation_response = {}

    try:
        task.prepare_for_task(
            dataset=minimal_dataset,
            input_columns=inputs_names,
            output_columns=outputs_names,
        )
        validation_response["dataset_status"] = "valid"
    except (TypeError, ValueError) as e:
        validation_response["dataset_status"] = "invalid"
        validation_response["error"] = str(e)
    return validation_response


def _validate_splits(splits: str, component_registry: "ComponentRegistry") -> None:
    """Validate a splits payload against the schema of its splitter.

    The payload carries the splitter's schema parameters at the top level. Any
    parameter the caller left out is filled with the schema placeholder, which
    is the value the frontend form would have submitted, so a manual split
    (which carries row indexes instead of proportions) validates too.

    Parameters
    ----------
    splits : str
        The splits payload, serialized as JSON.
    component_registry : ComponentRegistry
        Registry used to resolve the splitter named in the payload.

    Raises
    ------
    HTTPException
        If the payload is not valid JSON, names a splitter that is not
        registered, or carries parameters the splitter schema rejects.
    """
    import json

    try:
        splits_data = normalize_splits_payload(json.loads(splits))
    except (TypeError, ValueError) as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"splits is not a valid JSON object: {e}",
        ) from e

    splitter_name = splits_data.get("splitter_name")
    if splitter_name not in component_registry:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Splitter {splitter_name} does not exist in the registry.",
        )

    splitter_class = component_registry[splitter_name]["class"]
    parameters = {
        key: value for key, value in splits_data.items() if key not in META_KEYS
    }
    try:
        splitter_class.SCHEMA.model_validate(
            {**schema_placeholder_defaults(splitter_class), **parameters}
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid configuration for splitter {splitter_name}: {e}",
        ) from e


@router.post("/", status_code=status.HTTP_201_CREATED)
@inject
async def create_model_session(
    params: ModelSessionParams,
    session_factory: "sessionmaker" = Depends(lambda: di["session_factory"]),
    component_registry: "ComponentRegistry" = Depends(lambda: di["component_registry"]),
):
    """Create a new model session.

    Parameters
    ----------
    params : ModelSessionParams
        The new model session parameters.
    session_factory : Callable[..., ContextManager[Session]]
        A factory that creates a context manager that handles a SQLAlchemy session.
        The generated session can be used to access and query the database.
    component_registry : ComponentRegistry
        Registry used to resolve the splitter named in the splits payload.

    Returns
    -------
    ModelSession
        The created model session.

    Raises
    ------
    HTTPException
        If the splits payload is not valid for the selected splitter.
    HTTPException
        If the dataset with id dataset_id is not registered in the DB.
    """
    import os

    import pyarrow as pa
    import pyarrow.ipc as ipc

    _validate_splits(params.splits, component_registry)

    with session_factory() as db:
        try:
            dataset = db.get(Dataset, params.dataset_id)
            if not dataset:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found"
                )
            dataset_path = f"{dataset.file_path}/dataset"
            data_filepath = os.path.join(dataset_path, "data.arrow")

            with pa.OSFile(data_filepath, "rb") as source:
                reader = ipc.open_file(source)
                schema = reader.schema
                column_names = schema.names

            if len(params.input_columns + params.output_columns) > len(column_names):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Column index out of range",
                )

            model_session = ModelSession(
                dataset_id=params.dataset_id,
                task_name=params.task_name,
                name=params.name,
                input_columns=params.input_columns,
                output_columns=params.output_columns,
                train_metrics=params.train_metrics,
                validation_metrics=params.validation_metrics,
                test_metrics=params.test_metrics,
                evaluation_strategy=params.evaluation_strategy,
                splits=params.splits,
            )
            db.add(model_session)
            db.commit()
            db.refresh(model_session)
            return model_session
        except exc.IntegrityError as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Model session with name '{params.name}' already exists.",
            ) from e
        except exc.SQLAlchemyError as e:
            log.exception(e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal database error",
            ) from e


@router.delete("/")
@inject
async def delete_model_sessions(
    params: ModelSessionBulkDeleteParams,
    session_factory: "sessionmaker" = Depends(lambda: di["session_factory"]),
):
    """Delete multiple model sessions, in a single transaction.

    Parameters
    ----------
    params : ModelSessionBulkDeleteParams
        The IDs of the model sessions to delete. IDs that do not match an
        existing model session are silently skipped rather than failing the
        whole request.
    session_factory : Callable[..., ContextManager[Session]]
        A factory that creates a context manager that handles a SQLAlchemy session.
        The generated session can be used to access and query the database.

    Returns
    -------
    Response with code 204 NO_CONTENT
    """
    with session_factory() as db:
        try:
            for model_session_id in params.ids:
                model_session = db.get(ModelSession, model_session_id)
                if not model_session:
                    continue
                db.delete(model_session)

            db.commit()
            return Response(status_code=status.HTTP_204_NO_CONTENT)
        except exc.SQLAlchemyError as e:
            log.exception(e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal database error",
            ) from e


@router.delete("/{model_session_id}")
@inject
async def delete_model_session(
    model_session_id: int,
    session_factory: "sessionmaker" = Depends(lambda: di["session_factory"]),
):
    """Delete the model session associated with the provided ID from the database.

    Parameters
    ----------
    model_session_id : int
        ID of the model session to be deleted.
    session_factory : Callable[..., ContextManager[Session]]
        A factory that creates a context manager that handles a SQLAlchemy session.
        The generated session can be used to access and query the database.

    Returns
    -------
    Response with code 204 NO_CONTENT
    """
    import os

    with session_factory() as db:
        try:
            model_session = db.get(ModelSession, model_session_id)
            if not model_session:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Model session not found",
                )

            # Snapshot the on-disk paths of the runs that the FK cascade is
            # about to delete, so they can be cleaned up after the commit.
            runs = db.query(Run).filter(Run.model_session_id == model_session_id).all()
            paths_to_clean = [
                path
                for run in runs
                for path in (
                    run.run_path,
                    run.plot_history_path,
                    run.plot_slice_path,
                    run.plot_contour_path,
                    run.plot_importance_path,
                )
            ]

            db.delete(model_session)
            db.commit()
        except exc.SQLAlchemyError as e:
            log.exception(e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal database error",
            ) from e

    # Best-effort disk cleanup, done only once the DB delete has committed:
    # a cleanup failure here must not undo an otherwise-successful deletion.
    for path in paths_to_clean:
        if path and os.path.exists(path):
            try:
                remove_path(path)
            except (OSError, ValueError) as e:
                log.warning(f"Failed to delete path {path}: {e}")

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.patch("/{model_session_id}")
@inject
async def update_model_session(
    model_session_id: int,
    dataset_id: Union[int, None] = None,
    task_name: Union[str, None] = None,
    name: Union[str, None] = None,
    session_factory: "sessionmaker" = Depends(lambda: di["session_factory"]),
):
    """Update the model session associated with the provided ID.

    Parameters
    ----------
    model_session_id : int
        ID of the model session to update.
    session_factory : Callable[..., ContextManager[Session]]
        A factory that creates a context manager that handles a SQLAlchemy session.
        The generated session can be used to access and query the database.

    Returns
    -------
    Dict
        A dictionary containing the updated model session record.
    """
    with session_factory() as db:
        try:
            model_session = db.get(ModelSession, model_session_id)
            if model_session is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Model session not found",
                )

            # Validate name if provided
            if name is not None:
                if not name or not name.strip():
                    raise HTTPException(
                        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                        detail="Name cannot be empty",
                    )

                new_name = name.strip()

                # Check if name is different from current name
                if new_name != model_session.name:
                    # Check if name already exists
                    exists = db.execute(
                        select(ModelSession.id).where(
                            ModelSession.name == new_name,
                            ModelSession.id != model_session_id,
                        )
                    ).scalar()
                    if exists:
                        raise HTTPException(
                            status_code=status.HTTP_409_CONFLICT,
                            detail="Model session name already exists",
                        )
                    setattr(model_session, "name", new_name)

            if dataset_id:
                setattr(model_session, "dataset_id", dataset_id)
            if task_name:
                setattr(model_session, "task_name", task_name)

            if dataset_id or task_name or name:
                db.commit()
                db.refresh(model_session)
                return model_session
            else:
                raise HTTPException(
                    status_code=status.HTTP_304_NOT_MODIFIED,
                    detail="Record not modified",
                )
        except HTTPException:
            raise
        except exc.IntegrityError as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Model session name already exists",
            ) from e
        except exc.SQLAlchemyError as e:
            db.rollback()
            log.exception(e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal database error",
            ) from e
