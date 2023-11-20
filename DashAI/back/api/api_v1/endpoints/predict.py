import json
import logging
import os
from typing import Any, List

import pandas as pd
from datasets import Dataset
from fastapi import APIRouter, Depends, UploadFile, status
from fastapi.exceptions import HTTPException
from sqlalchemy import exc
from sqlalchemy.orm import Session

from DashAI.back.api.api_v1.schemas.predict_params import PredictParams
from DashAI.back.api.deps import get_db
from DashAI.back.core.config import component_registry, settings
from DashAI.back.database.models import Dataset as Dt
from DashAI.back.database.models import Experiment, Run
from DashAI.back.dataloaders.classes.dataloader import BaseDataLoader, to_dashai_dataset
from DashAI.back.models.base_model import BaseModel

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)

router = APIRouter()


@router.get("/")
async def get_prediction():
    """Placeholder for prediction get.

    Raises
    ------
    HTTPException
        Always raises exception as it was intentionally not implemented.
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Method not implemented"
    )


@router.post("/")
async def perform_predict(
    input_file: UploadFile,
    params: PredictParams = Depends(),
    db: Session = Depends(get_db),
) -> List[Any]:
    """
    Endpoint to perform model prediction for a particular run, given some
    sample values.

    Parameters
    ----------
    input_file: UploadFile
        File containing the sample data to be used for prediction.
        The format of the sample data must match the format of the data set used to
        train the run.
    run_id: int
        Id of the run to be used to predict.

    Returns
    -------
    list
        A list with the predictions given by the run.
        The type of each prediction is given by the task associated with the run.
    Raises
    ------
    HTTPException
        If run_id does not exist in the database.
        If experiment_id assoc. with the run does not exist in the database.
        If dataset_id assoc. with the experiment does not exist in the database.
    """
    try:
        run: Run = db.get(Run, params.run_id)
        if not run:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Run not found"
            )

        exp: Experiment = db.get(Experiment, run.experiment_id)
        if not exp:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Experiment not found"
            )

        # TODO: Use only experiment
        dat: Dt = db.get(Dt, exp.dataset_id)
        if not dat:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found"
            )
    except exc.SQLAlchemyError as e:
        log.exception(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal database error",
        ) from e

    model = component_registry[run.model_name]["class"]
    trained_model: BaseModel = model.load(run.run_path)

    # Load Dataset using Dataloader
    tmp_path = os.path.join(
        settings.USER_DATASET_PATH, "tmp_predict", str(params.run_id)
    )
    try:
        os.makedirs(tmp_path, exist_ok=True)
    except FileExistsError as e:
        log.exception(e)
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A dataset with this name already exists",
        ) from e
    dataloader: BaseDataLoader = component_registry["JSONDataLoader"]["class"]()
    raw_dataset = dataloader.load_data(
        filepath_or_buffer=input_file, temp_path=tmp_path, params={"data_key": "data"}
    )
    input_df = pd.DataFrame(raw_dataset["train"])
    # TODO: Use feature_names from Experiment
    input_df = input_df.reindex(columns=json.loads(dat.feature_names))
    raw_dataset["train"] = Dataset.from_pandas(input_df)

    # Transform into DashAIDataset
    dataset = to_dashai_dataset(raw_dataset, raw_dataset["train"].column_names, [])

    y_pred = trained_model.predict(dataset["train"])

    return y_pred.tolist()


@router.delete("/")
async def delete_prediction():
    """Placeholder for prediction delete.

    Raises
    ------
    HTTPException
        Always raises exception as it was intentionally not implemented.
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Method not implemented"
    )


@router.patch("/")
async def update_prediction():
    """Placeholder for prediction update.

    Raises
    ------
    HTTPException
        Always raises exception as it was intentionally not implemented.
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Method not implemented"
    )