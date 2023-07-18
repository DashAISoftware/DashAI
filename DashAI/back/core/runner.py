import logging
import os
from typing import Dict, List

from sqlalchemy import exc
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
        try:
            # Prepare dataset
            prepared_dataset = task.prepare_for_task(dataset)

        except Exception as e:
            log.exception(e)
            run.set_status_as_error()
            db.commit()
            # Close DB connection
            db.close()
            raise RunnerError(
                "Preparation of the dataset failed",
            ) from e

        run.set_status_as_started()
        db.commit()

        try:
            # Training
            model.fit(prepared_dataset["train"])
        except Exception as e:
            log.exception(e)
            run.set_status_as_error()
            db.commit()
            # Close DB connection
            db.close()
            raise RunnerError(
                "Model training failed",
            ) from e

        run.set_status_as_finished()
        db.commit()

        try:
            # Evaluation
            model_metrics = {
                split: {
                    metric.__name__: metric.score(
                        prepared_dataset[split],
                        model.predict(prepared_dataset[split]),
                    )
                    for metric in metrics
                }
                for split in ["train", "validation", "test"]
            }
        except Exception as e:
            log.exception(e)
            run.set_status_as_error()
            db.commit()
            # Close DB connection
            db.close()
            raise RunnerError(
                "Metrics calculation failed",
            ) from e

        # Save the changes in the run
        run.train_metrics = model_metrics["train"]
        run.validation_metrics = model_metrics["validation"]
        run.test_metrics = model_metrics["test"]

        try:
            os.makedirs(settings.USER_RUN_PATH, exist_ok=True)
            run_path = f"{settings.USER_RUN_PATH}/{run.id}"
            model.save(run_path)
        except Exception as e:
            log.exception(e)
            run.set_status_as_error()
            db.commit()
            raise RunnerError(
                "Model saving failed",
            ) from e
        run.run_path = run_path
        db.commit()
    except exc.SQLAlchemyError as e:
        log.exception(e)
        run.set_status_as_error()
        db.commit()
        raise RunnerError(
            "Connection with the database failed",
        ) from e
    finally:
        # Close DB connection
        db.close()
