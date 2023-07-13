import json
import logging
from typing import Dict

import pandas as pd
from fastapi import APIRouter, Body, Depends, status
from fastapi.exceptions import HTTPException
from sqlalchemy import exc
from sqlalchemy.orm import Session

from DashAI.back.api.deps import get_db
from DashAI.back.core.config import component_registry
from DashAI.back.database.models import Run

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)

router = APIRouter()


@router.post("/")
async def perform_predict(
    run_id: int,
    data: dict = Body(...),
    db: Session = Depends(get_db),
) -> Dict:
    """
    Endpoint to perform model prediction for a particular run, given some
    sample values.

    Parameters
    ----------
    rund_id: int
        Id of the run.
    data: dict
        Dictionary with a list of dictionaries with values for each feature.

    Returns
    -------
    dict[list]
        A dictionary with a list of predicted probabilities for each class.
        The list has dimensions (n_samples, n_classes).

    Raises
    ------
    HTTPException
        If run_id does not exist in the database
    """
    try:
        run: Run = db.get(Run, run_id)
        if not run:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Run not found"
            )
    except exc.SQLAlchemyError as e:
        log.exception(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal database error",
        ) from e

    run_path = run.run_path
    model = component_registry[run.model_name]["class"]
    trained_model = model.load(run_path)
    data = json.dumps(data["data"])

    # TODO: Save labels metadata
    x = pd.read_json(data, orient="records")
    y_pred = trained_model.predict_proba(x)

    results = {"Predictions": y_pred.tolist()}
    return results
