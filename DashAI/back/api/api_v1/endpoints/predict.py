import logging
from typing import Annotated

import numpy as np
import pandas as pd
from fastapi import APIRouter, Depends, Query, status
from fastapi.exceptions import HTTPException
from sqlalchemy import exc
from sqlalchemy.orm import Session

from DashAI.back.api.deps import get_db
from DashAI.back.core.config import component_registry
from DashAI.back.database.models import Dataset, Experiment, Run
from DashAI.back.dataloaders.classes.dashai_dataset import load_dataset

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)

router = APIRouter()


@router.post("/")
async def perform_predict(
    run_id: int,
    features: Annotated[list, Query()],
    values: Annotated[list, Query()],
    db: Session = Depends(get_db),
):
    try:
        run: Run = db.get(Run, run_id)
        if not run:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Run not found"
            )
        exp: Experiment = db.get(Experiment, run.experiment_id)
        if not exp:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Experiment not found"
            )
        dataset: Dataset = db.get(Dataset, exp.dataset_id)
        if not dataset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found"
            )
    except exc.SQLAlchemyError as e:
        log.exception(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal database error",
        ) from e

    # Dataset
    dataset = load_dataset(f"{dataset.file_path}/dataset")
    dataset_split = dataset["train"]

    # Run path
    run_path = run.run_path

    # Model
    run_model_class = component_registry[run.model_name]["class"]
    model = run_model_class(**run.parameters)
    trained_model = model.load(run_path)

    # Format predict data
    n_features = len(features)
    values_array = np.array(values).reshape(-1, n_features)
    values_df = pd.DataFrame(data=values_array, columns=features)

    # Predict
    y_preds = trained_model.predict_proba(values_df)

    # Format results
    results = {}
    for y_pred, n_sample in zip(y_preds, range(n_features), strict=True):
        label = np.argmax(y_pred)
        results[f"Sample {n_sample}"] = dataset_split.int2str_label(int(label))

    return results
