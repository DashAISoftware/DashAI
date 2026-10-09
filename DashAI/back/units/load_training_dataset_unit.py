"""Unit that loads the dataset a model was trained on."""

import logging
from typing import TYPE_CHECKING

from DashAI.back.job.base_job import JobError
from DashAI.back.units.base_unit import BaseUnit
from DashAI.back.units.context import ExecutionContext

if TYPE_CHECKING:
    from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset

log = logging.getLogger(__name__)


class LoadTrainingDatasetUnit(BaseUnit):
    """Load the dataset a model was trained on, under a key of its own.

    Deliberately not ``LoadDatasetUnit``: this dataset is not the one being
    transformed, it is a *reference* the prediction needs — the task decodes
    predicted class indexes against its labels, and its declared types become
    the schema of the saved result. Publishing it as ``dataset`` would collide
    with the dataset actually being predicted on, since ``PROVIDES`` is fixed
    per class and both would want the same key.

    Two outputs, with different rules on purpose: the live dataset is cached
    for the prediction step, while the types travel as a plain JSON-serializable
    mapping so the saving step never has to reopen the file. Nothing derived
    from the dataset *being predicted on* crosses this boundary.
    """

    PROVIDES = ("train_dataset", "train_dataset_types")
    RUNTIME_PARAMS = ("train_dataset_file_path",)

    def execute(self, ctx: ExecutionContext) -> None:
        from pathlib import Path

        from DashAI.back.dataloaders.classes.dashai_dataset import load_dataset

        file_path = self.config["train_dataset_file_path"]

        try:
            train_dataset: "DashAIDataset" = load_dataset(
                str(Path(f"{file_path}/dataset/"))
            )
        except Exception as e:
            log.exception(e)
            raise JobError(
                f"Cannot load training dataset from {file_path}/dataset/"
            ) from e

        ctx.put("train_dataset", train_dataset)
        ctx.put_ref(
            "train_dataset_types",
            {name: kind.to_string() for name, kind in train_dataset.types.items()},
        )
