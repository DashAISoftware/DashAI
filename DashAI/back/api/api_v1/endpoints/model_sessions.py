import logging
from typing import TYPE_CHECKING, Any, Dict, List, Union

from fastapi import APIRouter, Depends, Response, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import HTTPException
from kink import di, inject
from pydantic import BaseModel
from sqlalchemy import exc, select

from DashAI.back.api.api_v1.schemas.model_sessions_params import (
    ColumnsValidationParams,
    ModelSessionBulkDeleteParams,
    ModelSessionParams,
    SessionConverterParams,
    UpdateConvertersParams,
)
from DashAI.back.dependencies.database.models import Dataset, ModelSession

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
    from DashAI.back.types.utils import get_types_from_arrow_metadata

    with session_factory() as db:
        try:
            dataset = db.get(Dataset, params.dataset_id)
            if not dataset:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Dataset not found",
                )

            dataset_path = f"{dataset.file_path}/dataset"
            # A preprocessed session partition is saved as two separate
            # datasets, `x`/`y` (see `SessionPreprocessingJob.run()`), unlike
            # the raw dataset's single combined `data.arrow`.
            partition_is_split = False
            if params.model_session_id is not None:
                model_session = db.get(ModelSession, params.model_session_id)
                if model_session and model_session.preprocessed_path:
                    is_cv = (
                        model_session.evaluation_strategy
                        == "CrossValidationEvaluationStrategy"
                    )
                    relative = (
                        os.path.join("full_dataset", "train") if is_cv else "train"
                    )
                    partition_path = os.path.join(
                        model_session.preprocessed_path, relative
                    )
                    if os.path.isdir(partition_path):
                        dataset_path = partition_path
                        partition_is_split = True

            def _read_batch(base_path: str):
                data_filepath = os.path.join(base_path, "data.arrow")
                with pa.OSFile(data_filepath, "rb") as source:
                    reader = ipc.open_file(source)
                    return reader.get_batch(0)

            merged_types = None
            if partition_is_split:
                x_batch = _read_batch(os.path.join(dataset_path, "x"))
                y_batch = _read_batch(os.path.join(dataset_path, "y"))
                sample_size = min(5, x_batch.num_rows, y_batch.num_rows)
                table = pa.Table.from_batches([x_batch.slice(0, sample_size)])
                y_table = pa.Table.from_batches([y_batch.slice(0, sample_size)])
                for col_name in y_table.column_names:
                    table = table.append_column(col_name, y_table.column(col_name))
                # `x`/`y` are saved as separate Arrow files, each carrying its
                # own DashAI-types metadata blob for only its own columns.
                # `append_column` copies `table`'s (x's) schema metadata
                # verbatim, so `y`'s columns are missing from it unless the
                # two type dicts are merged explicitly here.
                merged_types = {
                    **get_types_from_arrow_metadata(x_batch.schema),
                    **get_types_from_arrow_metadata(y_batch.schema),
                }
            else:
                batch = _read_batch(dataset_path)
                sample_size = min(5, batch.num_rows)
                table = pa.Table.from_batches([batch.slice(0, sample_size)])

            minimal_dataset = DashAIDataset(table, types=merged_types)

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


@router.post("/", status_code=status.HTTP_201_CREATED)
@inject
async def create_model_session(
    params: ModelSessionParams,
    session_factory: "sessionmaker" = Depends(lambda: di["session_factory"]),
    job_queue=Depends(lambda: di["job_queue"]),
):
    """Create a new model session.

    If `params.converters` is non-empty, it is validated the same way
    `PUT /model-session/{id}/converters` validates it (every `input_scope`
    atom must resolve and be type-compatible — see
    `_validate_converter_configs`), rejecting the request with a 422 before
    any DB write. If it's non-empty *and* `input_columns`/`output_columns`
    are already finalized (non-empty) at creation time, a
    `SessionPreprocessingJob` is enqueued right away to fit/transform the
    converters and persist the resulting partitions to disk (see
    `preprocessing_status`/`preprocessed_path`). Unlike most jobs, this
    isn't triggered by a separate frontend call: there's no user decision
    involved — if converters are configured, they always need to be
    preprocessed before any Run can train on this session. A session
    created with converters but without final input/output columns yet
    (the wizard's Preprocessing step comes before its Columns step) is not
    enqueued here; it's enqueued later, when `update_model_session`
    finalizes those columns.

    Parameters
    ----------
    params : ModelSessionParams
        The new model session parameters.
    session_factory : Callable[..., ContextManager[Session]]
        A factory that creates a context manager that handles a SQLAlchemy session.
        The generated session can be used to access and query the database.
    job_queue : BaseJobQueue
        Injected job queue, used to enqueue the preprocessing job.

    Returns
    -------
    ModelSession
        The created model session.

    Raises
    ------
    HTTPException
        If the dataset with id dataset_id is not registered in the DB, or
        if `params.converters` fails validation.
    """
    import os

    import pyarrow as pa
    import pyarrow.ipc as ipc

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

            if params.converters:
                from DashAI.back.dataloaders.classes.dashai_dataset import (
                    get_columns_spec,
                )

                dataset_column_types = get_columns_spec(dataset_path)
                component_registry = di["component_registry"]
                _validate_converter_configs(
                    params.converters, dataset_column_types, component_registry
                )

            model_session = ModelSession(
                dataset_id=params.dataset_id,
                task_name=params.task_name,
                name=params.name,
                input_columns=[a.model_dump() for a in params.input_columns],
                output_columns=[a.model_dump() for a in params.output_columns],
                train_metrics=params.train_metrics,
                validation_metrics=params.validation_metrics,
                test_metrics=params.test_metrics,
                evaluation_strategy=params.evaluation_strategy,
                splits=params.splits,
                converters=[c.model_dump() for c in params.converters],
            )
            db.add(model_session)
            db.commit()
            db.refresh(model_session)

            if (
                model_session.converters
                and model_session.input_columns
                and model_session.output_columns
            ):
                from DashAI.back.job.session_preprocessing_job import (
                    SessionPreprocessingJob,
                )

                job = SessionPreprocessingJob(
                    kwargs={"model_session_id": model_session.id}
                )
                job.set_status_as_delivered()
                enqueued = job_queue.put(job)
                model_session.preprocessing_huey_id = enqueued.id
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
    with session_factory() as db:
        try:
            model_session = db.get(ModelSession, model_session_id)
            if not model_session:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Model session not found",
                )
            db.delete(model_session)
            db.commit()
            return Response(status_code=status.HTTP_204_NO_CONTENT)
        except exc.SQLAlchemyError as e:
            log.exception(e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal database error",
            ) from e


@router.patch("/{model_session_id}")
@inject
async def update_model_session(
    model_session_id: int,
    dataset_id: Union[int, None] = None,
    task_name: Union[str, None] = None,
    name: Union[str, None] = None,
    input_columns: Union[str, None] = None,
    output_columns: Union[str, None] = None,
    splits: Union[str, None] = None,
    evaluation_strategy: Union[str, None] = None,
    session_factory: "sessionmaker" = Depends(lambda: di["session_factory"]),
    job_queue=Depends(lambda: di["job_queue"]),
):
    """Update the model session associated with the provided ID.

    `input_columns`/`output_columns`/`splits` are JSON-encoded strings
    (matching the convention `ModelSessionParams.splits` already uses),
    e.g. `input_columns='["a","b"]'`. A converter's `input_scope` only ever
    references atoms (columns or earlier converters' groups), never real
    names tied to a specific split shape, so setting `splits` or
    `evaluation_strategy` no longer invalidates an existing converter list
    (the response's `converters_invalidated` field is always `False` now,
    kept for API compatibility). Instead, a `SessionPreprocessingJob` is
    enqueued to fit/transform the converters and persist the resulting
    partitions to disk (see
    `preprocessing_status`/`preprocessed_path`/`preprocessing_huey_id`)
    only when THIS SAME call is the one setting `input_columns`/
    `output_columns` (finalizing the wizard's Columns step) AND the
    resulting session ends up with non-empty `input_columns`,
    `output_columns`, AND `converters` (an explicit empty selection does
    not count). A later call that only touches unrelated fields — a bare
    rename, or a `splits`/`evaluation_strategy` change on a session that
    was already finalized by a previous call — never re-enqueues a job.
    The enqueue happens strictly after the columns/splits/strategy updates
    are committed, so the job (which opens its own DB session when it
    runs) reads the just-finalized row rather than racing it.

    Parameters
    ----------
    model_session_id : int
        ID of the model session to update.
    session_factory : Callable[..., ContextManager[Session]]
        A factory that creates a context manager that handles a SQLAlchemy session.
        The generated session can be used to access and query the database.
    job_queue : BaseJobQueue
        Injected job queue, used to enqueue the preprocessing job.

    Returns
    -------
    Dict
        A dictionary containing the updated model session record, plus a
        `converters_invalidated` boolean.
    """
    import json as json_module

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
            if input_columns is not None:
                model_session.input_columns = json_module.loads(input_columns)
            if output_columns is not None:
                parsed_output_columns = json_module.loads(output_columns)
                # A session's own `output_columns` must always be a literal
                # `column` atom, never a `group` atom: the raw dataset has to
                # be split into train/test *before* any converter runs, so a
                # converter-produced target value genuinely cannot exist yet
                # at split time. `SessionPreprocessingJob.run()` already
                # enforces exactly this rule, but only once the job is
                # actually running — the wizard's "create session" call would
                # otherwise return 200 OK and the session would fail
                # asynchronously, with nothing for the user to see. Checked
                # here too so the wizard gets a synchronous, immediate 422.
                # `input_columns` is deliberately not restricted this way:
                # group atoms remain fully supported there (the main use case
                # this feature exists for).
                if any(
                    isinstance(atom, dict) and atom.get("kind") == "group"
                    for atom in parsed_output_columns or []
                ):
                    raise HTTPException(
                        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                        detail=(
                            "output_columns cannot reference a converter's "
                            "group output; the target column must be an "
                            "original dataset column."
                        ),
                    )
                model_session.output_columns = parsed_output_columns

            # Converters reference `input_scope` atoms (columns or earlier
            # converters' groups), never real names tied to a specific split
            # shape, and nothing is fit until this endpoint's own
            # input_columns/output_columns branch below enqueues the real
            # preprocessing job. A split/strategy change alone therefore
            # never invalidates an already-configured converter list.
            converters_invalidated = False

            if splits is not None:
                model_session.splits = splits
            if evaluation_strategy is not None:
                model_session.evaluation_strategy = evaluation_strategy

            any_field_set = any(
                v is not None
                for v in (
                    dataset_id,
                    task_name,
                    name,
                    input_columns,
                    output_columns,
                    splits,
                    evaluation_strategy,
                )
            )
            if any_field_set:
                db.commit()
                db.refresh(model_session)

                # Enqueue only when THIS SAME call is the one setting
                # input_columns/output_columns (not any other call, like a
                # bare rename or a splits/strategy-only change on an
                # already-finalized session — see the brief), AND the
                # resulting values are all actually non-empty (an explicit
                # empty-list selection, e.g. `input_columns=[]`, must not
                # trigger a job either). Enqueuing only after the commit
                # above means the job's own DB session (opened fresh when
                # it runs) reads the just-finalized columns instead of
                # racing the pre-finalize row still on disk.
                if (
                    (input_columns is not None or output_columns is not None)
                    and model_session.converters
                    and model_session.input_columns
                    and model_session.output_columns
                ):
                    from DashAI.back.job.session_preprocessing_job import (
                        SessionPreprocessingJob,
                    )

                    job = SessionPreprocessingJob(
                        kwargs={"model_session_id": model_session.id}
                    )
                    job.set_status_as_delivered()
                    enqueued = job_queue.put(job)
                    model_session.preprocessing_huey_id = enqueued.id
                    db.commit()
                    db.refresh(model_session)

                response = jsonable_encoder(model_session)
                response["converters_invalidated"] = converters_invalidated
                return response
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


def _validate_converter_configs(
    converters: List[SessionConverterParams],
    dataset_column_types: Dict[str, Dict[str, str]],
    component_registry: "ComponentRegistry",
) -> None:
    """Validate a converters list without executing anything: every atom
    must be resolvable (a real dataset column, or a group produced by a
    converter already present earlier in the same list), and its declared
    type must be compatible with the converter it's being fed into.

    On top of atom resolvability and type compatibility, also rejects a
    "fit-once" converter (`SUPERVISED` and `CHANGES_ROW_COUNT` both False on
    its class — it fits a single instance on the `full_dataset` partition
    and reuses that instance transform-only on every other
    partition/fold) whose `input_scope` references the output group of a
    "fits-per-partition" converter (`SUPERVISED` or `CHANGES_ROW_COUNT` True
    on its class — it fits independently per partition/fold and can
    legitimately produce different real columns each time). That
    composition would silently apply one fold's fitted statistics to a
    different fold's different real columns. The reverse direction (a
    fits-per-partition converter referencing a fit-once converter's group)
    is fine, since the fit-once converter's group resolves to the same real
    columns on every partition.

    Raises
    ------
    HTTPException
        422, on the first invalid entry found.
    """
    from DashAI.back.converters.execution import instantiate_converter

    seen_ids: Dict[str, SessionConverterParams] = {}

    for entry in converters:
        if entry.id in seen_ids:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Duplicate converter id '{entry.id}'",
            )

        try:
            converter_instance = instantiate_converter(
                component_registry, entry.converter, entry.params
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid converter '{entry.converter}': {e}",
            ) from e

        metadata = type(converter_instance).get_metadata()
        allowed_types = metadata["allowed_types"]
        allowed_dtypes = metadata["allowed_dtypes"]
        non_allowed_dtypes = metadata["non_allowed_dtypes"]
        converter_is_fit_once = not (
            bool(getattr(type(converter_instance), "SUPERVISED", False))
            or bool(getattr(type(converter_instance), "CHANGES_ROW_COUNT", False))
        )

        for atom in entry.input_scope:
            if atom.kind == "column":
                if atom.name not in dataset_column_types:
                    raise HTTPException(
                        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                        detail=f"Column '{atom.name}' does not exist in the dataset",
                    )
                atom_type = dataset_column_types[atom.name]["type"]
                atom_dtype = dataset_column_types[atom.name].get("dtype")
            else:
                if atom.converter_id not in seen_ids:
                    raise HTTPException(
                        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                        detail=(
                            f"Converter '{atom.converter_id}' must be added "
                            "before its output can be referenced"
                        ),
                    )
                source_entry = seen_ids[atom.converter_id]
                source_instance = instantiate_converter(
                    component_registry, source_entry.converter, source_entry.params
                )
                source_is_fit_once = not (
                    bool(getattr(type(source_instance), "SUPERVISED", False))
                    or bool(getattr(type(source_instance), "CHANGES_ROW_COUNT", False))
                )
                if converter_is_fit_once and not source_is_fit_once:
                    raise HTTPException(
                        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                        detail=(
                            f"Converter '{entry.converter}' (id '{entry.id}') "
                            "fits once on the full dataset and reuses that "
                            "single fitted instance, transform-only, on "
                            "every partition/fold. It cannot reference the "
                            f"output group of '{source_entry.converter}' "
                            f"(id '{source_entry.id}'), which fits "
                            "independently per partition/fold and may "
                            "legitimately produce different real columns "
                            "on each one."
                        ),
                    )
                try:
                    slots = source_instance.get_output_slots()
                except Exception as e:
                    # The default `get_output_slots()` derives its single
                    # slot from `get_output_type()`, which some converters
                    # (the imbalanced-learn samplers, e.g. `SMOTEConverter`/
                    # `RandomUnderSamplerConverter`) raise
                    # `NotImplementedError` from — they resample rows
                    # instead of producing a declarable output type. A
                    # later converter referencing one of those as a `group`
                    # is a plausible chain (e.g. `SelectKBest` fed from a
                    # `SMOTEConverter`'s output) and used to surface as an
                    # unhandled 500. Guarded here the same way
                    # `BaseConverter.get_metadata()` already guards this
                    # exact call.
                    raise HTTPException(
                        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                        detail=(
                            f"Cannot determine the output structure of "
                            f"converter '{atom.converter_id}' "
                            f"('{source_entry.converter}'), so its output "
                            f"cannot be referenced by "
                            f"'{entry.converter}' (id '{entry.id}'): {e}"
                        ),
                    ) from e
                if atom.slot is None or atom.slot < 0 or atom.slot >= len(slots):
                    raise HTTPException(
                        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                        detail=(
                            f"Converter '{atom.converter_id}' has no slot {atom.slot}"
                        ),
                    )
                atom_type = type(slots[atom.slot]["type"]).__name__
                atom_dtype = None

            if allowed_types and atom_type not in allowed_types:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=(
                        f"Converter '{entry.converter}' does not accept type "
                        f"'{atom_type}'"
                    ),
                )
            if allowed_dtypes and atom_dtype and atom_dtype not in allowed_dtypes:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=(
                        f"Converter '{entry.converter}' does not accept dtype "
                        f"'{atom_dtype}'"
                    ),
                )
            if non_allowed_dtypes and atom_dtype in non_allowed_dtypes:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=(
                        f"Converter '{entry.converter}' does not accept dtype "
                        f"'{atom_dtype}'"
                    ),
                )

        seen_ids[entry.id] = entry


@router.put("/{model_session_id}/converters")
@inject
async def update_session_converters(
    model_session_id: int,
    params: UpdateConvertersParams,
    session_factory: "sessionmaker" = Depends(lambda: di["session_factory"]),
):
    """Replace a model session's converter list, validating every entry's
    column scope and type compatibility without executing anything.
    Preprocessing runs once, later, when the wizard's Columns step
    finalizes the session (see `update_model_session`). An empty list
    clears any previously applied converters and their persisted
    preprocessed data.

    Parameters
    ----------
    model_session_id : int
        ID of the model session to update.
    params : UpdateConvertersParams
        The new, complete converter list (replaces the existing one).
    session_factory : Callable[..., ContextManager[Session]]
        A factory that creates a context manager that handles a SQLAlchemy
        session.

    Returns
    -------
    ModelSession
        The updated model session.
    """
    with session_factory() as db:
        model_session = db.get(ModelSession, model_session_id)
        if model_session is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Model session not found",
            )

        if params.converters:
            from DashAI.back.core.enums.status import DatasetStatus
            from DashAI.back.dataloaders.classes.dashai_dataset import (
                get_columns_spec,
            )

            dataset = db.get(Dataset, model_session.dataset_id)
            if not dataset:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Dataset not found",
                )
            if dataset.status != DatasetStatus.FINISHED:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Dataset is not in finished state",
                )
            dataset_column_types = get_columns_spec(f"{dataset.file_path}/dataset")
            component_registry = di["component_registry"]
            _validate_converter_configs(
                params.converters, dataset_column_types, component_registry
            )

        model_session.converters = [c.model_dump() for c in params.converters]

        # Nothing re-runs the real preprocessing job until the wizard
        # finalizes (see `update_model_session`), so any successful edit
        # here — even a non-empty replacement list — invalidates whatever
        # preprocessed state a previous finalize may have produced; leaving
        # it in place would silently point at data that no longer reflects
        # the edited converter list.
        from DashAI.back.core.enums.status import SessionPreprocessingStatus

        model_session.preprocessed_path = None
        model_session.preprocessing_status = SessionPreprocessingStatus.NOT_STARTED
        model_session.preprocessing_huey_id = None

        db.commit()
        db.refresh(model_session)
        return model_session


class ConverterOutputSlotsQuery(BaseModel):
    converters: List[SessionConverterParams]


@router.post("/converters/output-slots")
@inject
async def get_converters_output_slots(
    payload: ConverterOutputSlotsQuery,
    component_registry: "ComponentRegistry" = Depends(lambda: di["component_registry"]),
) -> Dict[str, List[Dict[str, Any]]]:
    """Real output slots for a list of already-configured converters, each
    instantiated with its own actual `params` — unlike the generic
    `/component/{name}/` metadata (used to populate the wizard's atom
    list), which always reflects a converter's *default* params and so
    can never see that, say, a `SimpleImputer` configured in this specific
    session with `add_indicator=True` really declares a second output
    slot. Keyed by each entry's own `id` so callers can merge the result
    back onto the matching converter without depending on list order.

    A converter whose real `get_output_slots()` call fails (e.g. one that
    can't be instantiated with the given params, or whose output type
    isn't statically declarable) falls back to the same single generic
    "output" slot `get_metadata()` itself falls back to — this endpoint
    only ever refines the atom list's labels/types, so degrading to that
    default is safe.
    """
    from DashAI.back.converters.base_converter import BaseConverter
    from DashAI.back.converters.execution import instantiate_converter

    result: Dict[str, List[Dict[str, Any]]] = {}
    for entry in payload.converters:
        try:
            instance = instantiate_converter(
                component_registry, entry.converter, entry.params
            )
            slots = instance.get_output_slots()
        except Exception:
            slots = [{"slot": 0, "label": "output", "type": None}]
        result[entry.id] = BaseConverter.serialize_output_slots(slots)
    return result
