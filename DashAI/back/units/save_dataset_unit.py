"""Unit that persists the dataset in the context back to disk."""

import logging

from DashAI.back.job.base_job import JobError
from DashAI.back.units.base_unit import BaseUnit
from DashAI.back.units.context import ExecutionContext

log = logging.getLogger(__name__)


class SaveDatasetUnit(BaseUnit):
    """Write the dataset back to the path it was loaded from.

    Takes no configuration: the destination is ``dataset_path``, published by
    whichever unit loaded the dataset, so a save can never land somewhere the
    load did not come from. Declares no outputs — its result is on disk, not in
    the context.

    The error message keeps the original exception's text. A failure here is an
    infrastructure failure (out of space, permissions, a path the filesystem
    rejects), and only the message of the outermost error reaches the user: the
    job queue stores ``str(exc)``, never the ``__cause__`` chain. Swallowing it
    would drop the diagnosis exactly when it is needed.
    """

    REQUIRES = ("dataset", "dataset_path")
    PROVIDES = ()

    def execute(self, ctx: ExecutionContext) -> None:
        from DashAI.back.dataloaders.classes.dashai_dataset import save_dataset

        dataset = ctx.require("dataset")
        dataset_path = ctx.require("dataset_path")

        try:
            save_dataset(dataset, dataset_path)
        except Exception as e:
            log.exception(e)
            raise JobError(f"Can not save dataset to path {dataset_path}: {e}") from e
