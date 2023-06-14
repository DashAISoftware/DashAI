import logging
from typing import Dict, List

from sqlalchemy.orm import Session

from DashAI.back.core.config import settings
from DashAI.back.database.models import Run
from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset
from DashAI.back.metrics import BaseMetric
from DashAI.back.models import BaseModel
from DashAI.back.tasks import BaseTask

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)


class RunnerError(Exception):
    """Exception raised when the runner proccess fails."""


def execute_run(
    dataset: Dict[str, DashAIDataset],
    task: BaseTask,
    model: BaseModel,
    metrics: List[BaseMetric],
    run: Run,
    db: Session,
):
    try:
        # Prepare dataset
        prepared_dataset = task.prepare_for_task(dataset)
        # Format dataset: TBD move this to dataloader
        formated_dataset = model.format_data(prepared_dataset)
        # Training
        run.set_status_as_started()
        db.commit()
        model.fit(
            formated_dataset["train"]["input"], formated_dataset["train"]["output"]
        )
        run.set_status_as_finished()
        db.commit()
        # Evaluation
        model_metrics = {
            split: {
                metric.__name__: metric.score(
                    formated_dataset[split]["output"],
                    model.predict(formated_dataset[split]["input"]),
                )
                for metric in metrics
            }
            for split in ["train", "validation", "test"]
        }
        # Save the changes in the run
        run.train_metrics = model_metrics["train"]
        run.validation_metrics = model_metrics["train"]
        run.test_metrics = model_metrics["train"]
        run_path = f"{settings.USER_RUN_PATH}/{run.id}"
        model.save(run_path)
        run.run_path = run_path
        db.commit()
    except Exception as e:
        log.exception(e)
        run.set_status_as_error()
        db.commit()
        raise RunnerError(
            "Internal runner error",
        ) from e
    finally:
        # Close DB connection
        db.close()
