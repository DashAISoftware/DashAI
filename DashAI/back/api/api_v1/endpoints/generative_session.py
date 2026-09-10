import logging
from datetime import datetime
from typing import TYPE_CHECKING, Union

from fastapi import APIRouter, Depends, Header, HTTPException, status
from kink import di
from sqlalchemy import exc, select

from DashAI.back.api.api_v1.schemas.generative_session_params import (
    GenerativeSessionBulkDeleteParams,
    GenerativeSessionParams,
)
from DashAI.back.core.utils import localize
from DashAI.back.dependencies.database.models import (
    GenerativeProcess,
    GenerativeSession,
    GenerativeSessionParameterHistory,
    ProcessData,
)
from DashAI.back.dependencies.downloads.nested import missing_downloads
from DashAI.back.models.base_generative_model import BaseGenerativeModel
from DashAI.back.models.RAG.exceptions.base import RAGWorkflowError
from DashAI.back.services.RAG.cleanup_service import CleanupService
from DashAI.back.services.RAG.session_validation_service import (
    SessionValidationService,
)
from DashAI.back.tasks.base_generative_task import BaseGenerativeTask
from DashAI.back.tasks.RAG_task import RAGTask

if TYPE_CHECKING:
    from sqlalchemy.orm import sessionmaker

    from DashAI.back.dependencies.registry import ComponentRegistry


router = APIRouter()
log = logging.getLogger(__name__)


@router.post("/", status_code=status.HTTP_201_CREATED)
async def upload_generative_session(
    params: GenerativeSessionParams,
    accept_language: str | None = Header(default=None),
    session_factory: "sessionmaker" = Depends(lambda: di["session_factory"]),
    component_registry: "ComponentRegistry" = Depends(lambda: di["component_registry"]),
):
    """Create a new generative session and log the initial parameters in the history."""

    with session_factory() as db:
        try:
            # Check if the model is registered
            if params.model_name not in component_registry:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Model {params.model_name} is not registered.",
                )
            model_class = component_registry[params.model_name]["class"]

            # Guard: model requires download but has not been downloaded -> 409.
            # Reconcile against the filesystem so a model downloaded after startup
            # (in the worker process) is recognised without an API restart.
            if getattr(
                model_class, "REQUIRES_DOWNLOAD", False
            ) and not component_registry.refresh_download_status(params.model_name):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=(
                        f"Model {params.model_name} must be downloaded before use."
                    ),
                )

            # Check if the model is a subclass of GenerativeModel
            if not issubclass(model_class, BaseGenerativeModel):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Model {params.model_name} is not a valid "
                    f"generative model.",
                )

            # Check if the task is registered
            if params.task_name not in component_registry:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Task {params.task_name} is not registered.",
                )
            task_class = component_registry[params.task_name]["class"]

            # RAG: validate and normalise RAG-specific parameters, filling in
            # the components the caller did not choose.
            if task_class == RAGTask:
                try:
                    params.parameters = SessionValidationService(
                        db, component_registry
                    ).prepare_RAG_params(params.parameters, accept_language)
                except (ValueError, RAGWorkflowError) as e:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=str(e),
                    ) from e

            # A parameter may select another component that itself needs
            # downloading; block until every nested one is present. Runs after
            # the RAG defaults are applied so it sees the final configuration.
            nested_missing = missing_downloads(params.parameters, component_registry)
            if nested_missing:
                names = ", ".join(m["name"] for m in nested_missing)
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=(
                        f"These components must be downloaded before use: {names}."
                    ),
                )

            # Validate schema
            try:
                model_class.SCHEMA.model_validate(params.parameters)
            except ValueError as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid parameters for model {params.model_name}: {e}",
                ) from e

            # Check if the task is a subclass of BaseGenerativeTask
            if not issubclass(task_class, BaseGenerativeTask):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Task {params.task_name} is not a valid generative task.",
                )

            now = datetime.now()
            session = GenerativeSession(
                model_name=params.model_name,
                task_name=params.task_name,
                parameters=params.parameters,
                name=params.name,
                description=params.description,
                created=now,
                last_modified=now,
            )
            db.add(session)
            try:
                db.commit()
            except exc.IntegrityError as e:
                db.rollback()
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=(
                        f"Generative session with name '{params.name}' already exists."
                    ),
                ) from e
            db.refresh(session)

            session_params_entry = GenerativeSessionParameterHistory(
                session_id=session.id,
                parameters=session.parameters,
                model_name=session.model_name,
                modified_at=datetime.now(),
            )
            db.add(session_params_entry)
            db.commit()

            return {
                "id": session.id,
                "model_name": session.model_name,
                "task_name": session.task_name,
                "parameters": session.parameters,
                "name": session.name,
                "description": session.description,
                "created": session.created,
                "last_modified": session.last_modified,
                # Localized here so the client never receives a language object.
                "display_name": localize(
                    component_registry[session.task_name]["display_name"],
                    accept_language,
                ),
            }
        except exc.SQLAlchemyError as e:
            log.exception(e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal database error",
            ) from e


@router.get("/{session_id}", status_code=status.HTTP_200_OK)
async def get_generative_session(
    session_id: int,
    session_factory: "sessionmaker" = Depends(lambda: di["session_factory"]),
):
    """Get a generative session by its ID.

    Parameters
    ----------
    session_id : int
        The ID of the generative session to retrieve.
    session_factory : Callable[..., ContextManager[Session]]
        A factory that creates a context manager that handles a SQLAlchemy session.
        The generated session can be used to access and query the database.

    Returns
    -------
    dict
        A dictionary with the generative session on the database

    Raises
    ------
    HTTPException
        If the generative session does not exist or if there's an internal
        database error.
    """

    with session_factory() as db:
        try:
            session = db.get(GenerativeSession, session_id)
            if not session:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=(f"Generative session {session_id} does not exist in DB."),
                )
            return session
        except exc.SQLAlchemyError as e:
            log.exception(e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal database error",
            ) from e


@router.get("/", status_code=status.HTTP_200_OK)
async def get_all_generative_sessions(
    task_name: Union[str, None] = None,
    session_factory: "sessionmaker" = Depends(lambda: di["session_factory"]),
):
    """Get all generative sessions ordered by creation date.

    Parameters
    ----------
    task_name : str | None
        If given, return only sessions of that generative task. A view scoped to
        one task (the RAG entry point, say) uses this; the shared session list
        asks for everything and groups the result by task.
    session_factory : Callable[..., ContextManager[Session]]
        A factory that creates a context manager that handles a SQLAlchemy session.
        The generated session can be used to access and query the database.

    Returns
    -------
    list
        A list of dictionaries with the matching generative sessions, ordered by
        creation date.

    Raises
    ------
    HTTPException
        If there's an internal database error.
    """

    with session_factory() as db:
        try:
            query = db.query(GenerativeSession)
            if task_name is not None:
                query = query.filter(GenerativeSession.task_name == task_name)
            sessions = query.order_by(GenerativeSession.created.asc()).all()
        except exc.SQLAlchemyError as e:
            log.exception(e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal database error",
            ) from e

        session_list = []
        for session in sessions:
            session_list.append(
                {
                    "id": session.id,
                    "task_name": session.task_name,
                    "model_name": session.model_name,
                    "parameters": session.parameters,
                    "name": session.name,
                    "description": session.description,
                    "created": session.created,
                    "last_modified": session.last_modified,
                }
            )
        return session_list


@router.delete("/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_generative_sessions(
    params: GenerativeSessionBulkDeleteParams,
    session_factory: "sessionmaker" = Depends(lambda: di["session_factory"]),
):
    """Delete multiple generative sessions, in a single transaction.

    Parameters
    ----------
    params : GenerativeSessionBulkDeleteParams
        The IDs of the generative sessions to delete. IDs that do not match
        an existing session are silently skipped rather than failing the
        whole request.
    session_factory : Callable[..., ContextManager[Session]]
        A factory that creates a context manager that handles a SQLAlchemy session.
        The generated session can be used to access and query the database.

    Raises
    ------
    HTTPException
        If there's an internal database error.
    """

    with session_factory() as db:
        try:
            for session_id in params.ids:
                session = db.get(GenerativeSession, session_id)
                if not session:
                    continue

                # Delete all the processes associated with the session
                processes = (
                    db.query(GenerativeProcess)
                    .filter(GenerativeProcess.session_id == session_id)
                    .all()
                )
                # Delete all the process data associated with the processes
                for process in processes:
                    process_data = (
                        db.query(ProcessData)
                        .filter(ProcessData.process_id == process.id)
                        .all()
                    )
                    for data in process_data:
                        db.delete(data)
                # Delete the processes
                for process in processes:
                    db.delete(process)

                # Delete the session parameter history entries
                parameters_history = (
                    db.query(GenerativeSessionParameterHistory)
                    .filter(GenerativeSessionParameterHistory.session_id == session_id)
                    .all()
                )
                for entry in parameters_history:
                    db.delete(entry)

                # Finally, delete the session itself
                db.delete(session)

            db.commit()
        except exc.SQLAlchemyError as e:
            log.exception(e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal database error",
            ) from e
        except Exception as e:
            log.exception(e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error",
            ) from e
        finally:
            db.rollback()
            db.close()


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_generative_session(
    session_id: int,
    session_factory: "sessionmaker" = Depends(lambda: di["session_factory"]),
):
    """Delete a generative session by its ID.

    Parameters
    ----------
    session_id : int
        The ID of the generative session to delete.
    session_factory : Callable[..., ContextManager[Session]]
        A factory that creates a context manager that handles a SQLAlchemy session.
        The generated session can be used to access and query the database.

    Raises
    ------
    HTTPException
        If the generative session does not exist or if there's an internal
        database error.
    """

    with session_factory() as db:
        try:
            session = db.get(GenerativeSession, session_id)
            if not session:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Generative session {session_id} does not exist in DB.",
                )

            old_parameters = dict(session.parameters or {})

            # Delete all the processes associated with the session
            processes = (
                db.query(GenerativeProcess)
                .filter(GenerativeProcess.session_id == session_id)
                .all()
            )
            # Delete all the process data associated with the processes
            for process in processes:
                process_data = (
                    db.query(ProcessData)
                    .filter(ProcessData.process_id == process.id)
                    .all()
                )
                for data in process_data:
                    db.delete(data)
            # Delete the processes
            for process in processes:
                db.delete(process)

            # Delete the session parameter history entries
            parameters_history = (
                db.query(GenerativeSessionParameterHistory)
                .filter(GenerativeSessionParameterHistory.session_id == session_id)
                .all()
            )
            for entry in parameters_history:
                db.delete(entry)
            # Finally, delete the session itself
            db.delete(session)

            CleanupService(db).cleanup_orphaned_resources(session_id, old_parameters)
            db.commit()
        except HTTPException:
            raise
        except exc.SQLAlchemyError as e:
            log.exception(e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal database error",
            ) from e
        except Exception as e:
            log.exception(e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error",
            ) from e
        finally:
            db.close()


@router.patch("/{session_id}", status_code=status.HTTP_200_OK)
async def update_generative_session(
    session_id: int,
    name: Union[str, None] = None,
    description: Union[str, None] = None,
    model_name: Union[str, None] = None,
    session_factory: "sessionmaker" = Depends(lambda: di["session_factory"]),
    component_registry: "ComponentRegistry" = Depends(lambda: di["component_registry"]),
):
    """Update the generative session associated with the provided ID.

    Parameters
    ----------
    session_id : int
        ID of the generative session to update.
    name : Union[str, None], optional
        New name for the session.
    description : Union[str, None], optional
        New description for the session.
    model_name : Union[str, None], optional
        New model (component name) for the session. Must be a registered
        generative model; if it requires a download it must already be
        downloaded.
    session_factory : Callable[..., ContextManager[Session]]
        A factory that creates a context manager that handles a SQLAlchemy session.
        The generated session can be used to access and query the database.
    component_registry : ComponentRegistry
        The DashAI component registry, used to validate the new model.

    Returns
    -------
    Dict
        A dictionary containing the updated generative session record.

    Raises
    ------
    HTTPException
        If the session does not exist, the name is invalid or taken, or the new
        model is unknown, not a generative model, or not yet downloaded.
    """
    from DashAI.back.models.base_generative_model import BaseGenerativeModel

    with session_factory() as db:
        try:
            session = db.get(GenerativeSession, session_id)
            if session is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Generative session not found",
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
                if new_name != session.name:
                    # Check if name already exists
                    exists = db.execute(
                        select(GenerativeSession.id).where(
                            GenerativeSession.name == new_name,
                            GenerativeSession.id != session_id,
                        )
                    ).scalar()
                    if exists:
                        raise HTTPException(
                            status_code=status.HTTP_409_CONFLICT,
                            detail="Generative session name already exists",
                        )
                    setattr(session, "name", new_name)

            if description is not None:
                setattr(session, "description", description)

            # Validate and apply a model change if provided. A model may be
            # selected even when it is not downloaded yet; the chat blocks input
            # and offers a download until the weights become available.
            if model_name is not None and model_name != session.model_name:
                try:
                    model_class = component_registry[model_name]["class"]
                except KeyError as e:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Model {model_name} is not registered.",
                    ) from e
                if not issubclass(model_class, BaseGenerativeModel):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Model {model_name} is not a valid generative model.",
                    )

                # Resolve the parameters for the new model: reuse the most
                # recent parameters used for it in this session, else fall back
                # to the model's schema defaults (its field placeholders).
                last_used = (
                    db.query(GenerativeSessionParameterHistory)
                    .filter(
                        GenerativeSessionParameterHistory.session_id == session_id,
                        GenerativeSessionParameterHistory.model_name == model_name,
                    )
                    .order_by(GenerativeSessionParameterHistory.modified_at.desc())
                    .first()
                )
                if last_used is not None:
                    new_parameters = last_used.parameters
                else:
                    properties = model_class.get_schema().get("properties", {})
                    new_parameters = {
                        key: prop.get("placeholder") for key, prop in properties.items()
                    }

                session.model_name = model_name
                session.parameters = new_parameters
                db.add(
                    GenerativeSessionParameterHistory(
                        session_id=session.id,
                        parameters=new_parameters,
                        model_name=model_name,
                        modified_at=datetime.now(),
                    )
                )

            if name is not None or description is not None or model_name is not None:
                session.last_modified = datetime.now()
                db.commit()
                db.refresh(session)
                return session
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
                detail="Generative session name already exists",
            ) from e
        except exc.SQLAlchemyError as e:
            db.rollback()
            log.exception(e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal database error",
            ) from e


@router.put("/{session_id}/parameters", status_code=status.HTTP_200_OK)
async def update_generative_session_params(
    session_id: int,
    new_params: dict,
    session_factory: "sessionmaker" = Depends(lambda: di["session_factory"]),
    component_registry: "ComponentRegistry" = Depends(lambda: di["component_registry"]),
):
    with session_factory() as db:
        try:
            session = db.get(GenerativeSession, session_id)
            if not session:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Generative session {session_id} does not exist in DB.",
                )

            old_parameters = dict(session.parameters or {})
            try:
                task_class = component_registry[session.task_name]["class"]
            except KeyError as e:
                raise HTTPException(
                    status_code=404,
                    detail=(
                        f"Task '{session.task_name}' is not registered"
                        " in the component registry."
                    ),
                ) from e

            # ── RAG-specific validation of new_params ──
            if task_class is not None and task_class == RAGTask:
                try:
                    normalized = SessionValidationService(
                        db, component_registry
                    ).validate_update_payload(new_params)
                except (ValueError, RAGWorkflowError) as e:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
                    ) from e

                # Merge validated new params into old params
                updated_parameters = {**old_parameters, **normalized}

                # Cleanup orphaned RAG resources
                CleanupService(db).cleanup_orphaned_resources(
                    session_id, old_parameters, updated_parameters
                )
            else:
                # Non-RAG update: simple merge without RAG validation
                updated_parameters = {**old_parameters, **new_params}

            # ── Persist ──
            session_params_entry = GenerativeSessionParameterHistory(
                session_id=session.id,
                parameters=updated_parameters,
                model_name=session.model_name,
                modified_at=datetime.now(),
            )
            db.add(session_params_entry)

            session.parameters = updated_parameters
            session.last_modified = datetime.now()
            db.commit()
            db.refresh(session)

            return {"id": session.id, "parameters": session.parameters}
        except HTTPException:
            raise
        except exc.SQLAlchemyError as e:
            db.rollback()
            log.exception(e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal database error",
            ) from e


@router.get("/{session_id}/parameters-history", status_code=status.HTTP_200_OK)
async def get_generative_session_parameters_history(
    session_id: int,
    session_factory: "sessionmaker" = Depends(lambda: di["session_factory"]),
):
    """
    Get all parameter history entries for a generative session.

    Parameters
    ----------
    session_id : int
        The ID of the generative session to retrieve the parameter history for.
    session_factory : Callable[..., ContextManager[Session]]
        A factory that creates a context manager that handles a SQLAlchemy session.

    Returns
    -------
    list
        A list of dictionaries with all parameter history entries for the session.

    Raises
    ------
    HTTPException
        If the generative session does not exist or if there's an internal
        database error.
    """
    with session_factory() as db:
        try:
            # Check if the generative session exists
            session = db.get(GenerativeSession, session_id)
            if not session:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Generative session {session_id} does not exist in DB.",
                )

            # Get the session parameter history
            parameters_history = (
                db.query(GenerativeSessionParameterHistory)
                .filter(GenerativeSessionParameterHistory.session_id == session_id)
                .order_by(GenerativeSessionParameterHistory.modified_at.asc())
                .all()
            )

            # Convert the objects to dictionaries (explicit loop for clarity)
            history_list = []
            for entry in parameters_history:
                history_list.append(
                    {
                        "id": entry.id,
                        "session_id": entry.session_id,
                        "parameters": entry.parameters,
                        "modified_at": entry.modified_at,
                    }
                )
            return history_list
        except exc.SQLAlchemyError as e:
            log.exception(e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal database error",
            ) from e


@router.get("/parameters-history/{session_id}", status_code=status.HTTP_200_OK)
async def get_parameter_history_entry(
    session_id: int,
    session_factory: "sessionmaker" = Depends(lambda: di["session_factory"]),
):
    """
    Get history entry for a generative session by its ID.

    Parameters
    ----------
    session_id : int
        The ID of the generative session to retrieve.
    session_factory : Callable[..., ContextManager[Session]]
        A factory that creates a context manager that handles a SQLAlchemy session.
        The generated session can be used to access and query the database.

    Returns
    -------
    list
        A list of dictionaries with the parameter history entries for the session.

    Raises
    ------
    HTTPException
        If the generative session does not exist or if there's an internal
        database error.
    """

    with session_factory() as db:
        try:
            # Check if the generative session exists
            session = db.get(GenerativeSession, session_id)
            if not session:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Generative session {session_id} does not exist in DB.",
                )

            # Get the parameter history entry for the session
            parameters_history = (
                db.query(GenerativeSessionParameterHistory)
                .filter(GenerativeSessionParameterHistory.session_id == session_id)
                .order_by(GenerativeSessionParameterHistory.modified_at.asc())
                .all()
            )

            parameters_history = [p.__dict__ for p in parameters_history]
            if not parameters_history:
                return []

            events = []
            prev_params = parameters_history[0]["parameters"]
            prev_model = parameters_history[0].get("model_name")

            for i in range(1, len(parameters_history)):
                curr = parameters_history[i]
                curr_params = curr["parameters"]
                curr_model = curr.get("model_name")
                changes = []

                # A model switch resets parameters to the new model's own
                # values, so the raw parameter diff would be noise; report only
                # the model change for that entry.
                if curr_model and prev_model and curr_model != prev_model:
                    changes.append(
                        {
                            "parameter": "model",
                            "oldValue": prev_model,
                            "newValue": curr_model,
                        }
                    )
                else:
                    for key in curr_params:
                        old_val = prev_params.get(key)
                        new_val = curr_params[key]
                        if old_val != new_val:
                            changes.append(
                                {
                                    "parameter": key,
                                    "oldValue": old_val,
                                    "newValue": new_val,
                                }
                            )

                events.append(
                    {
                        "id": curr["id"],
                        "timestamp": curr["modified_at"],
                        "changes": changes,
                    }
                )
                prev_params = curr_params
                prev_model = curr_model

            return events

        except exc.SQLAlchemyError as e:
            log.exception(e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal database error",
            ) from e
