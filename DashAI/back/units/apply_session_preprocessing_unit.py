"""Unit that turns the rows to predict on into the rows the model expects."""

import logging
from typing import TYPE_CHECKING

from DashAI.back.job.base_job import JobError
from DashAI.back.units.base_unit import BaseUnit
from DashAI.back.units.context import ExecutionContext

if TYPE_CHECKING:
    from DashAI.back.preprocessing.session_preprocessor import SessionPreprocessor

log = logging.getLogger(__name__)

#: The preprocessor fitted on the session's whole training pool, which is the
#: one every prediction has to reuse. Written by ``PreprocessingJob`` next to
#: the per-fold ones, and the file ``load_final_preprocessor`` reads.
FINAL_PREPROCESSOR_FILENAME = "final.pkl"


class ApplySessionPreprocessingUnit(BaseUnit):
    """Publish the rows as the model was trained to see them.

    A session may declare preprocessing steps ahead of training. When it does,
    ``PreprocessingJob`` fits them once on the training data and persists the
    result, and the model is trained on the columns that fit produced rather
    than on the raw ones. Predicting on new rows then means applying that same
    fitted preprocessor, never refitting it on what is being predicted.

    The result goes under ``model_input`` instead of replacing ``dataset``: the
    raw rows are what a prediction is saved next to, so the two have to be
    live at once, the same way the training dataset keeps a key of its own.

    The unit always runs, and without an artifacts path it publishes the rows
    unchanged. That is what keeps the graph one shape whether or not a session
    preprocesses: the prediction step reads ``model_input`` in both cases, and
    what varies is this unit's configuration, not which units are wired.
    """

    REQUIRES = ("dataset",)
    PROVIDES = ("model_input",)
    RUNTIME_PARAMS = ("preprocessing_artifacts_path",)

    def execute(self, ctx: ExecutionContext) -> None:
        dataset = ctx.require("dataset")

        artifacts_path = self.config.get("preprocessing_artifacts_path")
        if artifacts_path:
            preprocessor = self._load_final_preprocessor(artifacts_path)
            dataset = preprocessor.transform_dataset(dataset)

        ctx.put("model_input", dataset)

    @staticmethod
    def _load_final_preprocessor(artifacts_path: str) -> "SessionPreprocessor":
        """Unpickle the preprocessor fitted on the session's training pool.

        Parameters
        ----------
        artifacts_path : str
            The session's ``preprocessing_artifacts_path``, the folder where
            ``PreprocessingJob`` left its fitted preprocessors.

        Returns
        -------
        SessionPreprocessor
            The fitted preprocessor, ready to transform without fitting.

        Raises
        ------
        JobError
            If the artifact cannot be read or unpickled.
        """
        import os
        import pickle

        artifact = os.path.join(artifacts_path, FINAL_PREPROCESSOR_FILENAME)
        try:
            with open(artifact, "rb") as f:
                return pickle.load(f)
        except Exception as e:
            log.exception(e)
            raise JobError(
                f"Cannot load the session preprocessor from {artifact}"
            ) from e
