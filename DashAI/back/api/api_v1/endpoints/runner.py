import logging
from typing import Dict

from fastapi import APIRouter, Depends, status
from fastapi.exceptions import HTTPException
from sqlalchemy import exc
from sqlalchemy.orm import Session

from DashAI.back.api.deps import get_db
from DashAI.back.core.config import model_registry
from DashAI.back.database.models import Dataset, Experiment, Run
from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset, load_dataset

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)

router = APIRouter()
metric_register = None  # TBD


@router.post("/")
async def execute_run(run_id: int, db: Session = Depends(get_db)):
    """
    Train and evaluate the given run.

    Parameters
    ----------
    run_id : int
        id of the run to query, train and evaluate.

    """
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
        dat: Dataset = db.get(Dataset, exp.dataset_id)
        if not dat:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found"
            )
    except exc.SQLAlchemyError as e:
        log.exception(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal database error",
        )
    run_instance = model_registry[run.model_name](run.parameters)
    dataset_dict = load_dataset(f"{dat.file_path}/dataset")
    # Training
    run_instance.fit(dataset_dict["train"]["x"], dataset_dict["train"]["y"])
    # Evaluation
    metrics = metric_register.task_to_components(exp.task_name)
    run.train_metrics: Dict[str, DashAIDataset] = {
        metric.name: metric.calc(
            dataset_dict["train"]["y"],
            run_instance.predict(dataset_dict["train"]["x"]),
        )
        for metric in metrics
    }
    run.validation_metrics = {}
    run.test_metrics = {
        metric.name: metric.calc(
            dataset_dict["test"]["y"],
            run_instance.predict(dataset_dict["test"]["x"]),
        )
        for metric in metrics
    }
