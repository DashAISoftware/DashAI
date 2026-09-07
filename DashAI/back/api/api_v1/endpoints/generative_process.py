import logging
from typing import TYPE_CHECKING, Any, Dict

from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import FileResponse
from kink import di
from sqlalchemy import exc
from starlette.datastructures import UploadFile
from typing_extensions import Annotated

from DashAI.back.dependencies.database.models import (
    GenerativeProcess,
    GenerativeSession,
    ProcessData,
)

if TYPE_CHECKING:
    from sqlalchemy.orm import sessionmaker

    from DashAI.back.dependencies.registry import ComponentRegistry
    from DashAI.back.tasks.base_generative_task import BaseGenerativeTask

router = APIRouter()
log = logging.getLogger(__name__)


@router.post("/", status_code=status.HTTP_201_CREATED)
async def upload_generative_process(
    request: Request,
    session_id: Annotated[int, Form(...)],
    session_factory: "sessionmaker" = Depends(lambda: di["session_factory"]),
    config: Dict[str, Any] = Depends(lambda: di["config"]),
):
    """Create a new generative session.

    Parameters
    ----------
    request : Request
        The incoming HTTP request containing form data and files.
    session_id : int
        The ID of the generative session to which this process belongs.
    session_factory : Callable[..., ContextManager[Session]]
        A factory that creates a context manager that handles a SQLAlchemy session.
        The generated session can be used to access and query the database.
    config : Dict[str, Any]
        A dictionary containing configuration settings, including the path for images.

    Returns
    -------
    dict
        A dictionary with the new generative session on the database
        and the input/output data.

    Raises
    ------
    HTTPException
        If there's an internal database error or if the session ID does not exist.
    """
    form = await request.form()
    input_items = []

    # Filter and sort only indexed keys like 'text_0', 'file_1'
    indexed_keys = [key for key in form if "_" in key and key.split("_")[1].isdigit()]
    for key in sorted(indexed_keys, key=lambda x: int(x.split("_")[1])):
        value = form[key]
        if isinstance(value, UploadFile):
            content = await value.read()
            input_items.append(content)  # raw image bytes
        else:
            input_items.append(str(value))  # text string

    with session_factory() as db:
        try:
            session = db.query(GenerativeSession).filter_by(id=session_id).first()
            if not session:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Session with ID {session_id} does not exist.",
                )

            task: "BaseGenerativeTask" = di["component_registry"][session.task_name][
                "class"
            ]()

            process = GenerativeProcess(
                session_id=session_id,
            )
            db.add(process)
            db.commit()
            db.refresh(process)

            processed_input = task.prepare_input_for_database(
                input_items, images_path=config["IMAGES_PATH"]
            )

            processed_data = []
            for data in processed_input:
                input_data = ProcessData(
                    data=data[0],
                    data_type=data[1],
                    is_input=True,
                    process_id=process.id,
                )
                processed_data.append(input_data)
            db.add_all(processed_data)
            db.commit()
            db.refresh(process)

            process = process.__dict__

            process["input"] = task.process_input_from_database(process["input"])

            return process
        except exc.SQLAlchemyError as e:
            log.exception(e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal database error",
            ) from e


@router.get("/{process_id}", status_code=status.HTTP_200_OK, response_model=None)
async def get_generative_process(
    process_id: int,
    session_factory: "sessionmaker" = Depends(lambda: di["session_factory"]),
    component_registry: "ComponentRegistry" = Depends(lambda: di["component_registry"]),
):
    """Get a generative process by its session ID.

    Parameters
    ----------
    process_id : str
        The ID of the generative process to retrieve.
    session_factory : Callable[..., ContextManager[Session]]
        A factory that creates a context manager that handles a SQLAlchemy session.
        The generated session can be used to access and query the database.

    Returns
    -------
    dict
        A dictionary with the generative process data.

    Raises
    ------
    HTTPException
        If the generative process is not found or if there's an internal database error.
    """
    with session_factory() as db:
        try:
            process = db.query(GenerativeProcess).filter_by(id=process_id).all()
            if not process:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Generative process with ID {process_id} does not exist.",
                )
            generative_session: GenerativeSession = db.get(
                GenerativeSession, process[0].session_id
            )

            task: "BaseGenerativeTask" = component_registry[
                generative_session.task_name
            ]["class"]()

            process = [p.__dict__ for p in process]

            process = [
                {
                    **p,
                    "input": task.process_input_from_database(p["input"]),
                    "output": task.process_output_from_database(p["output"]),
                }
                for p in process
            ]

            return process[0]
        except exc.SQLAlchemyError as e:
            log.exception(e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal database error",
            ) from e


@router.delete(
    "/{process_id}", status_code=status.HTTP_204_NO_CONTENT, response_model=None
)
async def delete_generative_process(
    process_id: int,
    session_factory: "sessionmaker" = Depends(lambda: di["session_factory"]),
):
    """Delete a generative process by its ID.

    Parameters
    ----------
    process_id : str
        The ID of the generative process to delete.
    session_factory : Callable[..., ContextManager[Session]]
        A factory that creates a context manager that handles a SQLAlchemy session.
        The generated session can be used to access and query the database.

    Returns
    -------
    None

    Raises
    ------
    HTTPException
        If the generative process is not found or if there's an internal database error.
    """
    with session_factory() as db:
        try:
            process = db.query(GenerativeProcess).filter_by(id=process_id).first()
            if not process:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Generative process with ID {process_id} does not exist.",
                )
            # Delete all associated input and output data
            db.query(ProcessData).filter_by(process_id=process.id).delete()
            # Delete the generative process itself
            db.delete(process)
            # Commit the changes to the database
            db.commit()
        except exc.SQLAlchemyError as e:
            log.exception(e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal database error",
            ) from e


@router.get(
    "/session/{session_id}", status_code=status.HTTP_200_OK, response_model=None
)
async def get_generative_process_by_session_id(
    session_id: int,
    session_factory: "sessionmaker" = Depends(lambda: di["session_factory"]),
    component_registry: "ComponentRegistry" = Depends(lambda: di["component_registry"]),
):
    """Get a generative process by its session ID.

    Parameters
    ----------
    session_id : str
        The ID of the generative process to retrieve.
    session_factory : Callable[..., ContextManager[Session]]
        A factory that creates a context manager that handles a SQLAlchemy session.
        The generated session can be used to access and query the database.

    Returns
    -------
    dict
        A dictionary with the generative process data.

    Raises
    ------
    HTTPException
        If the generative process is not found or if there's an internal database error.
    """

    with session_factory() as db:
        try:
            process = db.query(GenerativeProcess).filter_by(session_id=session_id).all()
            generative_session: GenerativeSession = db.get(
                GenerativeSession, session_id
            )

            task: "BaseGenerativeTask" = component_registry[
                generative_session.task_name
            ]["class"]()

            process = [p.__dict__ for p in process]

            process = [
                {
                    **p,
                    "input": task.process_input_from_database(p["input"]),
                    "output": task.process_output_from_database(p["output"]),
                }
                for p in process
            ]

            return process
        except exc.SQLAlchemyError as e:
            log.exception(e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal database error",
            ) from e


@router.get("/file/{filename}", status_code=200, response_model=None)
async def get_generative_file(
    filename: str,
    config: Dict[str, Any] = Depends(lambda: di["config"]),
):
    """Serve a generated media file with an auto-detected mime type.

    Handles every modality produced by generative tasks (image, audio,
    video) by resolving the file under ``IMAGES_PATH`` and returning it
    with the mime type guessed from its extension. Falls back to
    ``application/octet-stream`` when the extension is unknown.

    Parameters
    ----------
    filename : str
        The relative path or filename of the file to retrieve inside
        ``IMAGES_PATH``.
    config : Dict[str, Any]
        Application configuration container; must expose
        ``IMAGES_PATH`` (injected via ``kink``).

    Returns
    -------
    FileResponse
        The file served with a guessed mime type.

    Raises
    ------
    HTTPException
        404 if no file exists at the resolved path.
    """
    import mimetypes
    import os

    file_path = os.path.join(config["IMAGES_PATH"], filename)

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")

    media_type, _ = mimetypes.guess_type(file_path)
    return FileResponse(file_path, media_type=media_type or "application/octet-stream")
