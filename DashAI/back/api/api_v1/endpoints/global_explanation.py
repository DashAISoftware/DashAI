import logging
from typing import Callable

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, status
from fastapi.exceptions import HTTPException
from sqlalchemy import exc, select
from sqlalchemy.orm import Session
from typing_extensions import ContextManager

from DashAI.back.api.api_v1.schemas.explanation_params import GlobalExplanationParams
from DashAI.back.containers import Container
from DashAI.back.dependencies.database.models import GlobalExplanation, Run

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)

router = APIRouter()


@router.get("/")
@inject
async def get_global_explanations(
    run_id: int,
    session_factory: Callable[..., ContextManager[Session]] = Depends(
        Provide[Container.db.provided.session]
    ),
):
    """Return the available global explanations in the database.
    The global explanations can be filtered by run_id.

    Parameters
    ----------
    run_id: int
        Run id to select the global explanations to retrieve.
    session_factory : Callable[..., ContextManager[Session]]
        A factory that creates a context manager that handles a SQLAlchemy session.
        The generated session can be used to access and query the database.

    Returns
    -------
    List[dict]
        A list of dicts containing global explanations.

    Raises
    ------
    HTTPException
        If there are no global explanations associated with the run_id in the DB.
    """
    with session_factory() as db:
        try:
            global_explanations = db.scalars(
                select(GlobalExplanation).where(GlobalExplanation.run_id == run_id)
            ).all()

        except exc.SQLAlchemyError as e:
            log.exception(e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal database error",
            ) from e

    return global_explanations


@router.get("/{explanation_id}")
@inject
async def get_global_explanation_by_id(
    explanation_id: int,
    session_factory: Callable[..., ContextManager[Session]] = Depends(
        Provide[Container.db.provided.session]
    ),
):
    """Return the global explanation with id explanation_id from the database.

    Parameters
    ----------
    explainer_id : int
        id of the global explanation to query.

    session_factory : Callable[..., ContextManager[Session]]
        A factory that creates a context manager that handles a SQLAlchemy session.
        The generated session can be used to access and query the database.

    Returns
    -------
    dict
        Dict with the specified id.

    Raises
    ------
    HTTPException
        If the explainer with id explainer_id is not registered in the DB.
    """
    with session_factory() as db:
        try:
            global_explanation = db.get(GlobalExplanation, explanation_id)
            if not global_explanation:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Explainer not found",
                )

        except exc.SQLAlchemyError as e:
            log.exception(e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal database error",
            ) from e

    return global_explanation


@router.post("/", status_code=status.HTTP_201_CREATED)
@inject
async def upload_global_explanation(
    params: GlobalExplanationParams,
    session_factory: Callable[..., ContextManager[Session]] = Depends(
        Provide[Container.db.provided.session]
    ),
):
    """Endpoint to create a global explanation

    Parameters
    ----------
    name: string
        User's name for the explainer
    run_id: int
        Id of the run associated with the explainer
    explainer_name: str
        Selected explainer
    parameters: dict
        Explainer configuration parameters
    session_factory : Callable[..., ContextManager[Session]]
        A factory that creates a context manager that handles a SQLAlchemy session.
        The generated session can be used to access and query the database.

    Returns
    -------
    dict
        Dict with the new global explaination.

    Raises
    ------
    HTTPException
        If the explainer file cannot be saved.
    """
    with session_factory() as db:
        try:
            run: Run = db.get(Run, params.run_id)
            if not run:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="Run not found"
                )

            explanation = GlobalExplanation(
                name=params.name,
                run_id=params.run_id,
                explainer_name=params.explainer_name,
                parameters=params.parameters,
            )

            db.add(explanation)
            db.commit()
            db.refresh(explanation)

            return explanation

        except exc.SQLAlchemyError as e:
            log.exception(e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal database error",
            ) from e


@router.delete("/{explanation_id}")
@inject
async def delete_explainer(
    explanation_id: int,
    session_factory: Callable[..., ContextManager[Session]] = Depends(
        Provide[Container.db.provided.session]
    ),
):
    """Returns the global explanation with id explanation_id from the database.

    Parameters
    ----------
    explanation_id : int
        id of the global explaination to delete.
    session_factory : Callable[..., ContextManager[Session]]
        A factory that creates a context manager that handles a SQLAlchemy session.
        The generated session can be used to access and query the database.

    Raises
    ------
    HTTPException
        If the global explanation with id explanation_id is not registered in the DB.
    """
    with session_factory() as db:
        try:
            explanation = db.get(GlobalExplanation, explanation_id)
            if not explanation:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Explainer not found",
                )

            db.delete(explanation)
            db.commit()

        except exc.SQLAlchemyError as e:
            log.exception(e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal database error",
            ) from e


@router.patch("/")
async def update_component() -> None:
    """Update explanation.

    Raises
    ------
    HTTPException
        Always raises exception as it was intentionally not implemented.
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Method not implemented"
    )
