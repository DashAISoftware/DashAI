import logging

from fastapi import APIRouter, Depends, Response, status
from fastapi.exceptions import HTTPException
from sqlalchemy import exc
from sqlalchemy.orm import Session

from DashAI.back.api.api_v1.endpoints.components import _intersect_component_lists
from DashAI.back.api.deps import get_db
from DashAI.back.core.config import component_registry
from DashAI.back.core.runner import execute_run
from DashAI.back.database.models import Dataset, Experiment, Run
from DashAI.back.dataloaders.classes.dashai_dataset import load_dataset

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)

router = APIRouter()


@router.post("/")
async def perform_run_execution(run_id: int, db: Session = Depends(get_db)):
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
        )
    # Dataset
    dataset = load_dataset(f"{dataset.file_path}/dataset")

    # Model
    run_model_class = component_registry[run.model_name]["class"]
    model = run_model_class(**run.parameters)

    # Task
    task = component_registry[exp.task_name]["class"]()

    # Get evaluation Metrics
    metrics = _intersect_component_lists(
        component_registry.get_components_by_types(select="Metric"),
        component_registry.get_related_components(exp.task_name),
    ).values()

    # Mark run as delivered
    run.run_delivery()
    db.commit()

    # Execute the run
    execute_run(
        dataset=dataset, task=task, model=model, metrics=metrics, run=run, db=db
    )

    return Response(status_code=status.HTTP_202_ACCEPTED)
