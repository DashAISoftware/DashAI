import logging
from typing import TYPE_CHECKING, Union

from fastapi import APIRouter, Depends, File, Response, UploadFile, status
from fastapi.exceptions import HTTPException
from kink import di, inject
from pydantic import ValidationError
from sqlalchemy import exc, select

from DashAI.back.api.api_v1.schemas.model_sessions_params import (
    ColumnsValidationParams,
    ModelSessionBulkDeleteParams,
    ModelSessionParams,
    PreprocessingStructureParams,
    SessionExportParams,
)
from DashAI.back.api.utils import remove_path
from DashAI.back.core.schema_fields.utils import schema_placeholder_defaults
from DashAI.back.dependencies.database.models import Dataset, ModelSession, Run
from DashAI.back.job.preprocessing_job import PreprocessingJob
from DashAI.back.preprocessing.column_ref import ConverterSequence, RawColumnRef
from DashAI.back.preprocessing.structure import (
    StructureError,
    infer_structure,
    resolve_state_refs,
)
from DashAI.back.splitters.splits_payload import (
    META_KEYS,
    normalize_splits_payload,
)

if TYPE_CHECKING:
    from sqlalchemy.orm import sessionmaker

    from DashAI.back.dependencies.job_queues import BaseJobQueue
    from DashAI.back.dependencies.registry import ComponentRegistry
    from DashAI.back.tasks.base_task import BaseTask


logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)

router = APIRouter()

# Every concrete value type name that DashAIValue's wildcard covers (i.e. every
# DashAIValue subclass in DashAI/back/types/value_types.py), used so a task
# declaring the wildcard (e.g. ClassificationTask) still accepts a converter
# group whose declared type is one of these, not just "DashAIValue" itself.
_DASHAI_VALUE_TYPE_NAMES = {
    "Integer",
    "Float",
    "Text",
    "Time",
    "Timestamp",
    "Duration",
    "Decimal",
    "Date",
    "Binary",
}


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


def _load_sample_dataset(db, dataset_id: int):
    """Load the first rows of a dataset, enough for its columns and types.

    Parameters
    ----------
    db : Session
        An open database session.
    dataset_id : int
        The dataset to load.

    Returns
    -------
    DashAIDataset
        At most 5 rows of the dataset, with every column and its type.

    Raises
    ------
    HTTPException
        404 if the dataset is not registered.
    """
    import os

    import pyarrow as pa
    import pyarrow.ipc as ipc

    from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset

    dataset = db.get(Dataset, dataset_id)
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found",
        )
    data_filepath = os.path.join(f"{dataset.file_path}/dataset", "data.arrow")
    with pa.OSFile(data_filepath, "rb") as source:
        reader = ipc.open_file(source)
        batch = reader.get_batch(0)
        sample_batch = batch.slice(0, min(5, batch.num_rows))
    return DashAIDataset(pa.Table.from_batches([sample_batch]))


def _type_allowed(type_name, allowed_types) -> bool:
    """Whether a column type is one of a task's allowed input types.

    A task declaring the DashAIValue wildcard accepts every concrete value
    type; an unknown type (None) is let through, since only a fit can tell.
    """
    if not allowed_types or type_name is None:
        return True
    return type_name in allowed_types or (
        "DashAIValue" in allowed_types and type_name in _DASHAI_VALUE_TYPE_NAMES
    )


@router.post("/preprocessing/structure")
@inject
async def get_preprocessing_structure(
    params: PreprocessingStructureParams,
    component_registry: "ComponentRegistry" = Depends(lambda: di["component_registry"]),
    session_factory: "sessionmaker" = Depends(lambda: di["session_factory"]),
):
    """Estimate the dataset structure after every step of a converter chain.

    Read only: nothing is fit and nothing is stored. The session wizard calls
    it on every change to the chain, to offer only columns that exist at each
    step and to flag steps that cannot work.

    Parameters
    ----------
    params : PreprocessingStructureParams
        The dataset, the candidate and target columns, and the chain.

    Returns
    -------
    StructureResult
        The state after every step, their errors and warnings, and the final
        state.
    """
    with session_factory() as db:
        try:
            sample = _load_sample_dataset(db, params.dataset_id)
        except exc.SQLAlchemyError as e:
            log.exception(e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal database error",
            ) from e
    return infer_structure(
        dataset_types=sample.types,
        candidates=params.candidates,
        target=params.output_columns,
        steps=params.steps,
        component_registry=component_registry,
    )


@router.post("/validation")
@inject
async def validate_columns(
    params: ColumnsValidationParams,
    component_registry: "ComponentRegistry" = Depends(lambda: di["component_registry"]),
    session_factory: "sessionmaker" = Depends(lambda: di["session_factory"]),
):
    """Validate if dataset columns are compatible with a task.

    With `preprocessing`, every input ref is resolved against the chain's
    estimated final structure and its type checked against the task's input
    types; the original columns among them also go through the task's own
    validation, as without preprocessing.
    """
    with session_factory() as db:
        try:
            minimal_dataset = _load_sample_dataset(db, params.dataset_id)

            column_names = minimal_dataset.column_names

            group_refs = [
                ref for ref in (params.input_refs or []) if ref.kind == "group"
            ]

            if not group_refs and len(
                params.inputs_columns + params.outputs_columns
            ) > len(column_names):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Column index out of range",
                )

            inputs_names = (
                [r.name for r in params.input_refs if r.kind == "raw"]
                if params.input_refs
                else params.inputs_columns
            )
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

    if params.preprocessing:
        allowed_input_types = set(task.get_metadata().get("inputs_types", []))
        structure = infer_structure(
            dataset_types=minimal_dataset.types,
            candidates=list(column_names),
            target=outputs_names,
            steps=params.preprocessing,
            component_registry=component_registry,
        )
        if not structure.valid:
            return {
                "dataset_status": "invalid",
                "error": "The preprocessing chain has an invalid step.",
            }
        try:
            items = resolve_state_refs(
                params.input_refs or [], structure.final, set(outputs_names)
            )
        except StructureError as e:
            return {"dataset_status": "invalid", "error": e.message.code}
        for item in items:
            if not _type_allowed(item.type, allowed_input_types):
                return {
                    "dataset_status": "invalid",
                    "error": (
                        f"Input of type '{item.type}' is not one of the task's "
                        f"allowed input types {sorted(allowed_input_types)}."
                    ),
                }
    elif group_refs:
        # A ref to a converter's output only has a type through the chain's
        # estimated structure, which needs the preprocessing steps.
        return {
            "dataset_status": "invalid",
            "error": "References to converter outputs need the preprocessing steps.",
        }

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


def _validate_evaluation_strategy(
    task_name: str, evaluation_strategy: str, component_registry: "ComponentRegistry"
) -> type:
    """Check that a session's evaluation strategy is one its task offers.

    The wizard lists only the strategies the registry relates to the task, and
    this asks the same registry the same question, so a session the front
    builds always passes. What it stops is a session put together by hand with
    a strategy its task never offered: one that carves nothing on a task with
    a target, which would train without ever reading the target, or a holdout
    on a task without one. A run relies on this pairing to know from the
    strategy alone which units to chain.

    Parameters
    ----------
    task_name : str
        The session's task.
    evaluation_strategy : str
        The session's evaluation strategy.
    component_registry : ComponentRegistry
        Registry that relates tasks to the strategies they offer.

    Returns
    -------
    type
        The strategy class, so the caller can read what it declares.

    Raises
    ------
    HTTPException
        If the task is not registered, or the strategy is not one it offers.
    """
    if task_name not in component_registry:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Task {task_name} does not exist in the registry.",
        )

    offered = sorted(
        component["name"]
        for component in component_registry.get_related_components(task_name)
        if component.get("type") == "EvaluationStrategy"
    )
    if evaluation_strategy not in offered:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                f"Evaluation strategy {evaluation_strategy!r} is not available "
                f"for task {task_name}. Available strategies: {offered}."
            ),
        )
    return component_registry[evaluation_strategy]["class"]


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


def _validate_empty_splits(splits: str, evaluation_strategy: str) -> None:
    """Check that a session whose strategy carves nothing sends no splits.

    Such a strategy takes no splitter, so any payload would be stored and never
    used, while the front still reads it back to decide which partitions the
    session has. Only an empty JSON object is accepted.

    Parameters
    ----------
    splits : str
        The splits payload, serialized as JSON.
    evaluation_strategy : str
        The session's evaluation strategy, named in the error.

    Raises
    ------
    HTTPException
        If the payload is not valid JSON or is not an empty object.
    """
    import json

    try:
        splits_data = json.loads(splits)
    except (TypeError, ValueError) as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"splits is not a valid JSON object: {e}",
        ) from e

    if splits_data != {}:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                f"Evaluation strategy {evaluation_strategy} takes no splitter, "
                f"so splits must be an empty object, got {splits}."
            ),
        )


# A training-only resampler runs twice (PreprocessingJob and ModelJob replay
# the chain), so both runs must draw the same rows.
DEFAULT_RESAMPLING_SEED = 42


def _with_resampling_seeds(steps, component_registry):
    """Give every training-only resampling step without a seed a fixed one.

    Stored in the step's params, so it is visible in the session info. A
    seed the user chose is kept.

    Parameters
    ----------
    steps : list of ConverterStep
        The session's preprocessing steps, as submitted.
    component_registry : ComponentRegistry
        Resolves each step's converter class.

    Returns
    -------
    list of ConverterStep
        The steps, with `random_state` filled in where it was missing.
    """
    seeded = []
    for step in steps:
        converter_class = (
            component_registry[step.converter]["class"]
            if step.converter in component_registry
            else None
        )
        needs_seed = (
            converter_class is not None
            and getattr(converter_class, "ROWS_APPLY_TO", None) == "train"
            and step.params.get("random_state") is None
        )
        if needs_seed:
            step = step.model_copy(
                update={
                    "params": {**step.params, "random_state": DEFAULT_RESAMPLING_SEED}
                }
            )
        seeded.append(step)
    return seeded


def _check_preprocessing_structure(
    db, params, sequence, input_column_refs, component_registry
) -> None:
    """Reject a session whose chain or inputs cannot work, before creating it.

    Without this, the session would be created and its PreprocessingJob
    would only fail afterwards, with an error like a bare missing column
    name.

    Raises
    ------
    HTTPException
        422 with the estimated structure when a step is invalid, or with the
        error when an input ref points at something the chain does not
        produce (or consumed).
    """
    sample = _load_sample_dataset(db, params.dataset_id)
    structure = infer_structure(
        dataset_types=sample.types,
        candidates=list(sample.column_names),
        target=params.output_columns,
        steps=sequence.steps,
        component_registry=component_registry,
    )
    if not structure.valid:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "message": "The preprocessing chain has an invalid step.",
                "structure": structure.model_dump(mode="json"),
            },
        )
    try:
        resolve_state_refs(
            input_column_refs, structure.final, set(params.output_columns)
        )
    except StructureError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "message": "An input column does not exist after preprocessing.",
                "error": e.message.model_dump(mode="json"),
            },
        ) from e


@router.post("/", status_code=status.HTTP_201_CREATED)
@inject
async def create_model_session(
    params: ModelSessionParams,
    session_factory: "sessionmaker" = Depends(lambda: di["session_factory"]),
    component_registry: "ComponentRegistry" = Depends(lambda: di["component_registry"]),
    job_queue: "BaseJobQueue" = Depends(lambda: di["job_queue"]),
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

    strategy_class = _validate_evaluation_strategy(
        params.task_name, params.evaluation_strategy, component_registry
    )
    if getattr(strategy_class, "KIND", "holdout") == "full":
        # A strategy that carves nothing takes no splitter, so its splits
        # payload must be empty, and no session preprocessing, which is fitted
        # once per partition.
        _validate_empty_splits(params.splits, params.evaluation_strategy)
        if params.preprocessing:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=(
                    f"Evaluation strategy {params.evaluation_strategy} does not "
                    "take session preprocessing: it is fitted per partition, "
                    "and this strategy makes none."
                ),
            )
    else:
        _validate_splits(params.splits, component_registry)

    sequence = ConverterSequence(
        steps=_with_resampling_seeds(params.preprocessing, component_registry)
    )
    try:
        sequence.validate_scopes()
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        ) from e
    has_preprocessing = len(sequence.steps) > 0

    if has_preprocessing and not params.input_column_refs:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                "input_column_refs is required when preprocessing steps are provided"
            ),
        )

    input_column_refs = params.input_column_refs or [
        RawColumnRef(name=name) for name in params.input_columns
    ]

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

            if has_preprocessing:
                _check_preprocessing_structure(
                    db, params, sequence, input_column_refs, component_registry
                )

            # When preprocessing is configured, input_columns is only a
            # placeholder until PreprocessingJob resolves the real ones, so
            # it cannot be checked against the raw dataset's column count.
            if not has_preprocessing and len(
                params.input_columns + params.output_columns
            ) > len(column_names):
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
                preprocessing=sequence.model_dump(mode="json"),
                input_column_refs=[
                    ref.model_dump(mode="json") for ref in input_column_refs
                ],
                preprocessing_status="pending" if has_preprocessing else "ready",
            )
            db.add(model_session)
            db.commit()
            db.refresh(model_session)

            if has_preprocessing:
                job_id = job_queue.put(
                    PreprocessingJob(model_session_id=model_session.id)
                ).id
                model_session.preprocessing_job_id = str(job_id)
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
    component_registry: "ComponentRegistry" = Depends(lambda: di["component_registry"]),
):
    """Update the model session associated with the provided ID.

    Parameters
    ----------
    model_session_id : int
        ID of the model session to update.
    session_factory : Callable[..., ContextManager[Session]]
        A factory that creates a context manager that handles a SQLAlchemy session.
        The generated session can be used to access and query the database.
    component_registry : ComponentRegistry
        Registry used to check that a new task still offers the session's
        evaluation strategy.

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
                # The stored strategy must still be one the new task offers.
                if task_name != model_session.task_name:
                    _validate_evaluation_strategy(
                        task_name, model_session.evaluation_strategy, component_registry
                    )
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


@router.post("/import", status_code=status.HTTP_201_CREATED)
@inject
async def import_model_session(
    file: UploadFile = File(...),
    session_factory: "sessionmaker" = Depends(lambda: di["session_factory"]),
    component_registry: "ComponentRegistry" = Depends(lambda: di["component_registry"]),
    config=Depends(lambda: di["config"]),
    job_queue: "BaseJobQueue" = Depends(lambda: di["job_queue"]),
):
    """Create a new session, its dataset and runs from an uploaded ``.dashai``.

    Raises
    ------
    HTTPException
        400 if the file is not a usable DashAI session, 409 if it needs a
        newer DashAI or a missing plugin, 500 on any other failure.
    """
    import shutil
    import tempfile
    from pathlib import Path

    from fastapi.concurrency import run_in_threadpool

    from DashAI.back.model_package.manifest import (
        MissingPluginError,
        ModelPackageError,
        UnsupportedPackageFormatError,
    )
    from DashAI.back.session_package.load import import_session_package

    workdir = Path(tempfile.mkdtemp(prefix="dashai-upload-"))
    try:
        upload = workdir / "session.dashai"
        with open(upload, "wb") as handle:
            shutil.copyfileobj(file.file, handle)
        return await run_in_threadpool(
            import_session_package,
            upload,
            session_factory,
            component_registry,
            config,
            job_queue,
        )
    except (UnsupportedPackageFormatError, MissingPluginError) as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e)) from e
    except ModelPackageError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e
    except Exception as e:
        log.exception(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error importing the session",
        ) from e
    finally:
        shutil.rmtree(workdir, ignore_errors=True)


@router.get("/{model_session_id}/export/preview")
@inject
async def get_session_export_preview(
    model_session_id: int,
    session_factory: "sessionmaker" = Depends(lambda: di["session_factory"]),
):
    """What exporting the session would carry: its runs and the file size.

    Raises
    ------
    HTTPException
        404 if the session does not exist.
    """
    from DashAI.back.session_package.export import (
        SessionNotFoundError,
        export_preview,
    )

    try:
        return export_preview(model_session_id, session_factory)
    except SessionNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Session not found"
        ) from e


@router.post("/{model_session_id}/export")
@inject
async def export_model_session(
    model_session_id: int,
    params: SessionExportParams,
    session_factory: "sessionmaker" = Depends(lambda: di["session_factory"]),
    component_registry: "ComponentRegistry" = Depends(lambda: di["component_registry"]),
):
    """Download the session and the chosen runs as a ``.dashai`` file.

    Raises
    ------
    HTTPException
        404 if the session does not exist, 409 if the chosen runs cannot be
        exported, 500 on any other failure.
    """
    import shutil
    import tempfile
    from pathlib import Path

    from fastapi.concurrency import run_in_threadpool
    from fastapi.responses import FileResponse
    from starlette.background import BackgroundTask

    from DashAI.back.session_package.export import (
        SessionNotExportableError,
        SessionNotFoundError,
        build_session_package,
        session_filename,
    )

    workdir = Path(tempfile.mkdtemp(prefix="dashai-export-"))
    destination = workdir / "session.dashai"
    try:
        manifest = await run_in_threadpool(
            build_session_package,
            model_session_id,
            params.run_ids,
            params.include_trained_models,
            destination,
            session_factory,
            component_registry,
        )
    except SessionNotFoundError as e:
        shutil.rmtree(workdir, ignore_errors=True)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Session not found"
        ) from e
    except SessionNotExportableError as e:
        shutil.rmtree(workdir, ignore_errors=True)
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e)) from e
    except Exception as e:
        shutil.rmtree(workdir, ignore_errors=True)
        log.exception(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error exporting the session",
        ) from e

    return FileResponse(
        destination,
        media_type="application/zip",
        filename=session_filename(manifest["info"]["session_name"]),
        background=BackgroundTask(shutil.rmtree, workdir, ignore_errors=True),
    )
