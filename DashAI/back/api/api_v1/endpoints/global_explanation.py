import logging
from typing import Union

from fastapi import APIRouter, Depends, status
from fastapi.exceptions import HTTPException
from sqlalchemy import exc, select
from sqlalchemy.orm import Session

from DashAI.back.api.api_v1.schemas.explanation_params import GlobalExplanationParams
from DashAI.back.api.deps import get_db
from DashAI.back.database.models import GlobalExplanation, Run

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)

router = APIRouter()


@router.get("/")
async def get_global_explanations(
    run_id: Union[int, None] = None,
    db: Session = Depends(get_db),
):
    """Return the available global explanations in the database.
    The global explanations can be filtered by run_id.

    Parameters
    ----------
    run_id: Union[int, None], optional
        If specified, the function will return all the explainers associated with
        the run, by default None.
    Returns
    -------
    List[dict]
        A list of dict containing explainers.

    Raises
    ------
    HTTPException
    """
    try:
        if run_id is not None:
            global_explanations = db.scalars(
                select(GlobalExplanation).where(GlobalExplanation.run_id == run_id)
            ).all()
        else:
            global_explanations = db.query(GlobalExplanation).all()

    except exc.SQLAlchemyError as e:
        log.exception(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal database error",
        ) from e

    return global_explanations


@router.get("/{explanation_id}")
async def get_global_explanation_by_id(
    explanation_id: int, db: Session = Depends(get_db)
):
    """Return the global explanation with id explanation_id from the database.

    Parameters
    ----------
    explainer_id : int
        id of the global explanation to query.

    Returns
    -------
    dict
        Dict with the specified id.

    Raises
    ------
    HTTPException
        If the explainer with id explainer_id is not registered in the DB.
    """
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
async def upload_global_explanation(
    params: GlobalExplanationParams,
    db: Session = Depends(get_db),
):
    """Endpoint to create an explanation

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

    Returns
    -------
    dict
        Dict with the new explainer.

    Raises
    ------
    HTTPException
        If the explainer file cannot be saved.
    """
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
async def delete_explainer(explanation_id: int, db: Session = Depends(get_db)):
    """Returns the explanation with id explanation_id from the database.

    Parameters
    ----------
    explanation_id : int
        id of the explaination to delete.

    Raises
    ------
    HTTPException
        If the global explanation with id explanation_id is not registered in the DB.
    """
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
async def update_component():
    """Update explanation placeholder.

    Raises
    ------
    HTTPException
        Always raises exception as it was intentionally not implemented.
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Method not implemented"
    )
