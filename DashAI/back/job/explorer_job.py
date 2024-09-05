import logging
import os
import pathlib
import pickle

from kink import inject
from sqlalchemy import exc
from sqlalchemy.orm import Session

from DashAI.back.dataloaders.classes.dashai_dataset import (
    DashAIDataset,
    load_dataset,
    select_columns,
)
from DashAI.back.dependencies.database.models import Dataset, Explorer
from DashAI.back.dependencies.registry import ComponentRegistry
from DashAI.back.exploration.base_explorer import BaseExplorer
from DashAI.back.job.base_job import BaseJob, JobError

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)


class ExplorerJob(BaseJob):
    """ExplorerJob class to launch explorations."""

    def set_status_as_delivered(self) -> None:
        """Set the status of the explorer as delivered."""
        explorer_id: int = self.kwargs["explorer_id"]
        db: Session = self.kwargs["db"]

        explorer: Explorer = db.query(Explorer).get(explorer_id)

        if explorer is None:
            raise JobError(f"Explorer with id {explorer_id} not found.")

        try:
            explorer.set_status_as_delivered()
            db.commit()
        except exc.SQLAlchemyError as e:
            log.exception(e)
            raise JobError(
                "Error while setting the status of the explorer as delivered."
            ) from e

    @inject
    def run(
        self,
        component_registry: ComponentRegistry = lambda di: di["component_registry"],
        config: dict = lambda di: di["config"],
    ) -> None:
        explorer_id: int = self.kwargs["explorer_id"]
        db: Session = self.kwargs["db"]

        # Load the explorer information
        try:
            explorer_info: Explorer = db.query(Explorer).get(explorer_id)
            if explorer_info is None:
                raise JobError(f"Explorer with id {explorer_id} not found.")
            explorer_info.set_status_as_started()
            db.commit()
        except exc.SQLAlchemyError as e:
            log.exception(e)
            raise JobError("Error while loading the explorer info.") from e

        # Load the dataset information
        try:
            dataset_info: Dataset = db.query(Dataset).get(explorer_info.dataset_id)
            if dataset_info is None:
                raise JobError(f"Dataset with id {explorer_info.dataset_id} not found.")
        except exc.SQLAlchemyError as e:
            log.exception(e)
            explorer_info.set_status_as_error()
            db.commit()
            raise JobError("Error while loading the dataset info.") from e

        # Load the dataset and select the columns
        try:
            dataset_dict: DashAIDataset = load_dataset(
                f"{dataset_info.file_path}/dataset"
            )
        except Exception as e:
            log.exception(e)
            explorer_info.set_status_as_error()
            db.commit()
            raise JobError(
                f"Can not load dataset from path {dataset_info.file_path}",
            ) from e

        # Select the columns
        try:
            cols: dict = explorer_info.columns
            columns = list(cols.keys())
            dataset_dict = select_columns(dataset_dict, columns, [])[0]
        except Exception as e:
            log.exception(e)
            explorer_info.set_status_as_error()
            db.commit()
            raise JobError(
                f"Error while selecting the columns {columns} from the dataset."
            ) from e

        # obtain the explorer component from the registry
        try:
            explorer_component_class = component_registry[
                explorer_info.exploration_type
            ]["class"]
        except KeyError as e:
            log.exception(e)
            explorer_info.set_status_as_error()
            db.commit()
            raise JobError(
                f"Explorer {explorer_info.exploration_type} not found in the registry."
            ) from e

        # Instance the explorer (the explorer handles its validation)
        try:
            explorer_instance: BaseExplorer = explorer_component_class(
                **explorer_info.parameters
            )
        except Exception as e:
            log.exception(e)
            explorer_info.set_status_as_error()
            db.commit()
            raise JobError(
                f"Error instancing the explorer {explorer_info.exploration_type}."
            ) from e

        # Launch the exploration
        try:
            result = explorer_instance.launch_exploration(dataset_dict["train"])
        except Exception as e:
            log.exception(e)
            explorer_info.set_status_as_error()
            db.commit()
            raise JobError(
                f"Error launching the exploration {explorer_info.exploration_type}."
            ) from e

        # Save the result
        try:
            if callable(getattr(explorer_instance, "save_exploration", None)):
                # save with class method in its own folder
                save_path = pathlib.Path(
                    os.path.join(
                        config["EXPLORATIONS_PATH"],
                        f"{explorer_info.exploration_type}/",
                    )
                )
                if not save_path.exists():
                    save_path.mkdir(parents=True, exist_ok=True)
                save_path = explorer_instance.save_exploration(
                    explorer_info, save_path, result
                )
                if isinstance(save_path, str):
                    save_path = pathlib.Path(save_path)
                if not isinstance(save_path, pathlib.Path):
                    raise JobError(
                        (
                            f"Error while saving the exploration"
                            f" {explorer_info.exploration_type}"
                            f", save path is not a pathlib.Path."
                        )
                    )
            else:
                # Save with pickle
                save_path = pathlib.Path(
                    os.path.join(
                        config["EXPLORATIONS_PATH"],
                        f"{explorer_info.exploration_type}_{explorer_id}.pickle",
                    )
                )
                with open(save_path, "wb") as f:
                    pickle.dump(result, f)
            # Update the explorer info
            explorer_info.exploration_path = save_path.as_posix()
            explorer_info.set_status_as_finished()
            db.commit()
        except Exception as e:
            log.exception(e)
            explorer_info.set_status_as_error()
            db.commit()
            raise JobError(
                f"Error while saving the exploration {explorer_info.exploration_type}."
            ) from e
