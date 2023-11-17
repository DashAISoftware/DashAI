import logging
import os
from typing import Union

from fastapi import APIRouter, Depends, Response, status
from fastapi.exceptions import HTTPException
from sqlalchemy import exc, select
from sqlalchemy.orm import Session

from DashAI.back.api.api_v1.schemas.explainer_params import ExplainerParams
from DashAI.back.api.deps import get_db
from DashAI.back.core.config import component_registry
from DashAI.back.database.models import Run, Explanation
from DashAI.back.api.utils import parse_params

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)

router = APIRouter()


@router.post("/explain", status_code=status.HTTP_201_CREATED)
async def upload_run(
    params: ExplainerParams,
    db: Session = Depends(get_db),
):
    """
    Endpoint to create a run.

    Parameters
    ----------
    run_id : int
        Id of the run linked to the explainer.
    explainer_name : str
        Name of the Explainer.
    parameters : dict

    Returns
    -------
    dict
        A dictionary with the new run on the database

    Raises
    ------
    HTTPException
        If the experiment with id experiment_id is not registered in the DB.
    """
    try:
        run = db.get(Run, params.run_id)
        if not run:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Run not found"
            )

        parsed_params = parse_params(ExplainerParams, params)
        explainer = component_registry[parsed_params.explainer]["class"]()

    except exc.SQLAlchemyError as e:
        log.exception(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal database error",
        ) from e
