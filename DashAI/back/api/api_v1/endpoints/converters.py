import logging
from typing import TYPE_CHECKING, Any, Dict

from fastapi import APIRouter, Depends, status
from fastapi.exceptions import HTTPException
from kink import di, inject
from sqlalchemy import exc

from DashAI.back.api.api_v1.schemas import converter_params as schemas

if TYPE_CHECKING:
    from sqlalchemy.orm.session import sessionmaker

    from DashAI.back.dependencies.database.models import Notebook
    from DashAI.back.dependencies.job_queues import BaseJobQueue
    from DashAI.back.dependencies.registry import ComponentRegistry

logger = logging.getLogger(__name__)
router = APIRouter()


def validate_converter_for_notebook(
    component_registry: "ComponentRegistry",
    notebook: "Notebook",
    converter_name: str,
    parameters: Dict[str, Any],
) -> None:
    """Check that a converter can run on a notebook before it is saved.

    On a document notebook each scope column names a content type and may
    narrow it to some element kinds. The converter's declared type
    restrictions are checked against the document columns spec, where the
    Text items form a ``Text`` column and the images an ``Image`` column.

    Parameters
    ----------
    component_registry : ComponentRegistry
        Registry holding the converter classes.
    notebook : Notebook
        The notebook the converter is added to.
    converter_name : str
        The converter class name.
    parameters : Dict[str, Any]
        The serialized converter parameters with ``scope`` and ``target``.

    Raises
    ------
    HTTPException
        404 when the converter is not registered, 422 when it does not run on
        the notebook's data kind, and 400 when a document scope is empty,
        names items the document does not have, sets a target, breaks the
        converter's type restrictions, or the converter changes the row
        count without being a DocumentConverter.
    """
    from DashAI.back.converters.document_converter import DocumentConverter
    from DashAI.back.core.column_constraints import columns_satisfy_metadata
    from DashAI.back.core.data_kinds import (
        DOCUMENT,
        document_type_error,
        supports_data_kind,
    )
    from DashAI.back.dataloaders.classes.document_items import (
        check_selection,
        selection_from_columns,
    )
    from DashAI.back.dataloaders.classes.notebook_data import (
        get_notebook_columns_spec,
        notebook_data_path,
    )

    if converter_name not in component_registry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Converter {converter_name} not found",
        )
    converter_class = component_registry[converter_name]["class"]
    if not supports_data_kind(converter_class, notebook.data_kind):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                f"Converter {converter_name} cannot run on a "
                f"{notebook.data_kind} notebook"
            ),
        )
    if notebook.data_kind != DOCUMENT:
        return
    if parameters.get("target") is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Converters on documents do not take a target column",
        )
    if converter_class.CHANGES_ROW_COUNT and not issubclass(
        converter_class, DocumentConverter
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Converter {converter_name} changes the number of rows, which "
                "only a DocumentConverter can do on a document"
            ),
        )
    scope = parameters.get("scope") or {}
    selection = selection_from_columns(scope.get("columns") or [])
    try:
        columns_spec = get_notebook_columns_spec(notebook)
        check_selection(selection, columns_spec, notebook_data_path(notebook))
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notebook data not found",
        ) from e
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e
    type_error = document_type_error(converter_class.get_metadata(), selection)
    if type_error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=type_error)
    if not columns_satisfy_metadata(
        converter_class.get_metadata(), list(selection), columns_spec
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "The selected content types do not satisfy the converter's "
                "type constraints"
            ),
        )


@router.post("/", status_code=status.HTTP_201_CREATED)
@inject
async def post_notebook_converter(
    params: schemas.ConverterParams,
    session_factory: "sessionmaker" = Depends(lambda: di["session_factory"]),
    component_registry: "ComponentRegistry" = Depends(lambda: di["component_registry"]),
):
    """Save a list of converters to apply to the notebook.

    Parameters
    ----------
    notebook_id : int
        ID of the notebook.
    converters : Dict[str, ConverterParams]
        A dictionary with the converters to apply to the notebook.
    session_factory : Callable[..., ContextManager[Session]]
        A factory that creates a context manager that handles a SQLAlchemy session.
        The generated session can be used to access and query the database.

    Returns
    -------
    dict
        A dictionary with the ID of the converter list.

    Raises
    ------
    HTTPException
        404 if the notebook or converter is not found, 422 or 400 when the
        converter cannot run on the notebook (see
        ``validate_converter_for_notebook``), 500 on a database error.
    """
    from DashAI.back.dependencies.database.models import Converter, Notebook

    with session_factory() as db:
        try:
            notebook = db.get(Notebook, params.notebook_id)
            if not notebook:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Notebook not found",
                )
            validate_converter_for_notebook(
                component_registry,
                notebook,
                params.converter,
                params.parameters.serialize(),
            )

            converter_name = params.converter
            converter_parameters = params.parameters.serialize()

            converter = Converter(
                notebook_id=params.notebook_id,
                converter=converter_name,
                parameters=converter_parameters,
            )

            db.add(converter)
            db.commit()
            db.refresh(converter)

            return converter

        except exc.SQLAlchemyError as e:
            logger.exception(e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal database error",
            ) from e


@router.get("/{converter_id}")
@inject
async def get_converter(
    converter_id: int,
    session_factory: "sessionmaker" = Depends(lambda: di["session_factory"]),
):
    """Get a converter list from the database.

    Parameters
    ----------
    converter_id : int
        ID of the converter list.
    session_factory : Callable[..., ContextManager[Session]]
        A factory that creates a context manager that handles a SQLAlchemy session.
        The generated session can be used to access and query the database.

    Returns
    -------
    Converter
        The converter list.

    Raises
    ------
    HTTPException
        If the converter list is not found or if there is an internal database error.
    """
    from DashAI.back.dependencies.database.models import Converter

    with session_factory() as db:
        try:
            converter = db.get(Converter, converter_id)
            if not converter:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Converter list not found",
                )

            return converter

        except exc.SQLAlchemyError as e:
            logger.exception(e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal database error",
            ) from e


@router.get("/notebook/{notebook_id}")
@inject
async def get_converters_by_notebook(
    notebook_id: int,
    session_factory: "sessionmaker" = Depends(lambda: di["session_factory"]),
):
    """Get a list of finished converters from the database by notebook ID.

    Parameters
    ----------
    notebook_id : int
        ID of the notebook.
    session_factory : Callable[..., ContextManager[Session]]
        A factory that creates a context manager that handles a SQLAlchemy session.
        The generated session can be used to access and query the database.

    Returns
    -------
    List[Converter]
        A list of converter lists.

    Raises
    ------
    HTTPException
        If there is an internal database error.
    """
    from DashAI.back.core.enums.status import ConverterStatus
    from DashAI.back.dependencies.database.models import Converter

    with session_factory() as db:
        try:
            converters = (
                db.query(Converter)
                .filter(Converter.notebook_id == notebook_id)
                .filter(Converter.status == ConverterStatus.FINISHED)
                .all()
            )
            return converters

        except exc.SQLAlchemyError as e:
            logger.exception(e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal database error",
            ) from e


@router.delete("/{converter_id}")
@inject
async def delete_converter(
    converter_id: int,
    session_factory: "sessionmaker" = Depends(lambda: di["session_factory"]),
    job_queue: "BaseJobQueue" = Depends(lambda: di["job_queue"]),
):
    """Delete a converter and replay the converters created before it.

    The notebook's working copy, dataset or document, is restored from its
    source and the earlier converters are enqueued again in creation order.
    """
    from DashAI.back.dataloaders.classes.notebook_data import restore_notebook_data
    from DashAI.back.dependencies.database.models import Converter, Explorer
    from DashAI.back.job.converter_job import ConverterJob

    with session_factory() as db:
        try:
            converter = db.get(Converter, converter_id)
            if not converter:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Converter list not found",
                )
            notebook = converter.notebook

            previous_converters = (
                db.query(Converter)
                .filter(
                    Converter.notebook_id == converter.notebook_id,
                    Converter.created < converter.created,
                )
                .order_by(Converter.created)
                .all()
            )

            next_converters = (
                db.query(Converter)
                .filter(
                    Converter.notebook_id == converter.notebook_id,
                    Converter.created >= converter.created,
                )
                .all()
            )

            next_explorers = (
                db.query(Explorer)
                .filter(
                    Explorer.notebook_id == converter.notebook_id,
                    Explorer.created >= converter.created,
                )
                .all()
            )

            restore_notebook_data(notebook)

            previous_ids = [previous.id for previous in previous_converters]
            for previous in previous_converters:
                previous.set_status_as_delivered()

            for following in next_converters:
                db.delete(following)

            for explorer in next_explorers:
                db.delete(explorer)

            db.commit()

            job_ids = [
                job_queue.put(ConverterJob(converter_id=previous_id)).id
                for previous_id in previous_ids
            ]

            last_job_id = job_ids[-1] if job_ids else None
            return {"jobId": last_job_id}

        except exc.SQLAlchemyError as e:
            logger.exception(e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal database error",
            ) from e
