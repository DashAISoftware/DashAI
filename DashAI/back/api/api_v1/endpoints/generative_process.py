import logging

from fastapi import APIRouter, Depends, HTTPException, status
from kink import di
from sqlalchemy import exc
from sqlalchemy.orm import sessionmaker

from DashAI.back.api.api_v1.schemas.generative_process_params import (
    GenerativeProcessParams,
)
from DashAI.back.dependencies.database.models import GenerativeProcess

router = APIRouter()
log = logging.getLogger(__name__)


@router.post("/", status_code=status.HTTP_201_CREATED)
async def upload_generative_process(
    params: GenerativeProcessParams,
    session_factory: sessionmaker = Depends(lambda: di["session_factory"]),
):
    """Create a new generative process.

    Parameters
    ----------
    params : GenerativeProcessParams
        The parameters of the new generative process, which includes the model name,
        parameters, process name and description.
    session_factory : Callable[..., ContextManager[Session]]
        A factory that creates a context manager that handles a SQLAlchemy session.
        The generated session can be used to access and query the database.

    Returns
    -------
    dict
        A dictionary with the new generative process on the database

    Raises
    ------
    HTTPException
        If there's an internal database error.
    """
    with session_factory() as db:
        try:
            process = GenerativeProcess(
                model_name=params.model_name,
                input_data=params.input_data,
                parameters=params.parameters,
                name=params.name,
                description=params.description,
            )
            db.add(process)
            db.commit()
            db.refresh(process)
            return process
        except exc.SQLAlchemyError as e:
            log.exception(e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal database error",
            ) from e
