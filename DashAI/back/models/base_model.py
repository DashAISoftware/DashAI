"""Base Model abstract class."""

import logging
import math
from abc import ABCMeta, abstractmethod
from typing import TYPE_CHECKING, Any, Dict, Final, final

from kink import di

from DashAI.back.config_object import ConfigObject
from DashAI.back.core.enums.metrics import LevelEnum, SplitEnum
from DashAI.back.dependencies.database.models import Metric

if TYPE_CHECKING:
    from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset

logger = logging.getLogger(__name__)


class BaseModel(ConfigObject, metaclass=ABCMeta):
    """Abstract base class for all machine learning models in DashAI.

    All models must extend this class and implement the abstract methods
    `save`, `load`, and `train`. The `calculate_metrics` and
    `prepare_dataset` methods provide optional hooks for subclasses.
    """

    TYPE: Final[str] = "Model"
    DISPLAY_NAME: str = ""
    DESCRIPTION: str = ""
    COLOR: str = "#795548"
    ICON: str = "Science"

    # Optional hook, set by an optimizer that wants to watch training as it goes.
    #
    # Signature: ``(results: dict[str, float], step: int) -> None``. It is called
    # once per epoch with the validation metrics of that epoch, and it may raise
    # to abort training early — that is how Optuna's pruning works.
    #
    # It lives here, on the base class, because every model with an epoch loop
    # already routes its per-epoch metrics through `calculate_metrics`. Hooking
    # the loops one by one would mean touching five files that do not share a
    # common ancestor, and missing any model added later.
    #
    # Models that train in a single shot never call `calculate_metrics` with
    # `level=EPOCH`, so for them this stays None and nothing changes.
    _epoch_reporter = None

    @classmethod
    def get_metadata(cls) -> Dict[str, Any]:
        """Get metadata values for the current model.

        Returns
        -------
        Dict[str, Any]
            Dictionary containing UI metadata such as the
            model icon used in the DashAI frontend.
        """
        metadata: Dict[str, Any] = {}
        metadata["icon"] = cls.ICON if cls.ICON else "Science"
        metadata["requires_download"] = bool(getattr(cls, "REQUIRES_DOWNLOAD", False))
        metadata["download_size_bytes"] = getattr(cls, "DOWNLOAD_SIZE_BYTES", None)
        return metadata

    @abstractmethod
    def save(self, filename: str) -> None:
        """Store the model to disk.

        Parameters
        ----------
        filename : str
            Path where the model will be saved.
        """
        raise NotImplementedError

    @abstractmethod
    def load(self, filename: str) -> Any:
        """Restore a model instance from disk.

        Parameters
        ----------
        filename : str
            Path where the model was previously saved.

        Returns
        -------
        Any
            The restored model instance.
        """
        raise NotImplementedError

    @abstractmethod
    def train(
        self,
        x_train: "DashAIDataset",
        y_train: "DashAIDataset",
        x_validation: "DashAIDataset" = None,
        y_validation: "DashAIDataset" = None,
    ) -> "BaseModel":
        """Train the model with the provided data.

        Parameters
        ----------
        x_train : DashAIDataset
            The input features for training.
        y_train : DashAIDataset
            The target labels for training.
        x_validation : DashAIDataset, optional
            Input features for
            validation. Defaults to None.
        y_validation : DashAIDataset, optional
            Target labels for
            validation. Defaults to None.

        Returns
        -------
        BaseModel
            The trained model instance.
        """
        raise NotImplementedError

    @final
    def _save_metrics(
        self,
        split: SplitEnum,
        level: LevelEnum,
        results: Dict[str, float],
        log_index: int = None,
        fold_index: int = None,
        inner_fold_index: int = None,
    ):
        """Persist computed metric values to the database.

        Handles step-index computation and upsert logic for LAST-level metrics.
        Called internally by `calculate_metrics` after scores are computed.

        Parameters
        ----------
        split : SplitEnum
            The data split the metrics belong to (TRAIN,
            VALIDATION, or TEST).
        level : LevelEnum
            The granularity level (LAST, TRIAL, STEP, or
            BATCH). LAST-level entries are upserted; others are inserted.
        results : Dict[str, float]
            Mapping of metric name to score value.
        log_index : int, optional
            Explicit step index for the entries.
            If None, the next index is derived from existing database
            entries. Defaults to None.
        """
        with di["session_factory"]() as db:
            # Initialize tracking dict if not exists
            if not hasattr(self, "_metric_step_counters"):
                self._metric_step_counters = {}

            # Create a unique key for this run/split/level combination
            counter_key = (self.run_id, split, level)

            # 1. Determine log_index
            if counter_key not in self._metric_step_counters:
                steps = (
                    db.query(Metric.step)
                    .filter_by(run_id=self.run_id, split=split, level=level)
                    .order_by(Metric.step.desc())
                    .limit(2)
                    .all()
                )

                if not steps:
                    current, previous = 0, 0
                elif len(steps) == 1:
                    current, previous = steps[0][0], 0
                else:
                    current, previous = steps[0][0], steps[1][0]

                self._metric_step_counters[counter_key] = {
                    "current": current,
                    "previous": previous,
                }

            counter = self._metric_step_counters[counter_key]

            current_max = counter["current"]
            previous_max = counter["previous"]

            # Compute delta (preserve spacing)
            delta = current_max - previous_max
            if delta <= 0:
                delta = 1

            # Case 1: no log_index -> advance naturally
            if log_index is None or log_index <= current_max:
                log_index = current_max + delta

            # Update the in-memory tracker
            counter["previous"] = current_max
            counter["current"] = log_index

            # 2. Handle 'LAST' level replacement logic
            if level == LevelEnum.LAST:
                for name, value in results.items():
                    existing = (
                        db.query(Metric)
                        .filter_by(
                            run_id=self.run_id, split=split, level=level, name=name
                        )
                        .first()
                    )

                    if existing:
                        existing.value = value
                        existing.step = log_index
                    else:
                        db.add(
                            Metric(
                                run_id=self.run_id,
                                split=split,
                                level=level,
                                name=name,
                                value=value,
                                step=log_index,
                            )
                        )

            # 3. Standard logging (STEP, BATCH, TRIAL) - just insert
            else:
                metric_entries = [
                    Metric(
                        run_id=self.run_id,
                        split=split,
                        level=level,
                        name=name,
                        value=score,
                        step=log_index,
                        fold_index=fold_index,
                        inner_fold_index=inner_fold_index,
                    )
                    for name, score in results.items()
                ]
                db.add_all(metric_entries)

            db.commit()

    @final
    def calculate_metrics(
        self,
        split: SplitEnum = SplitEnum.VALIDATION,
        level: LevelEnum = LevelEnum.LAST,
        log_index: int = None,
        x_data: "DashAIDataset" = None,
        y_data: "DashAIDataset" = None,
        fold_index: int = None,
        inner_fold_index: int = None,
    ):
        """Calculate and save metrics for a given data split and level.

        Parameters
        ----------
        split : SplitEnum
            The data split to evaluate (TRAIN, VALIDATION,
            or TEST). Defaults to SplitEnum.VALIDATION.
        level : LevelEnum
            The metric granularity level (LAST, TRIAL,
            STEP, or BATCH). Defaults to LevelEnum.LAST.
        log_index : int, optional
            Explicit step index for the metric
            entry. If None, the next step index is computed automatically.
            Defaults to None.
        x_data : DashAIDataset, optional
            Input features. If None, the
            dataset stored in the model for the given split is used.
            Defaults to None.
        y_data : DashAIDataset, optional
            Target labels. If None, the
            labels stored in the model for the given split are used.
            Defaults to None.
        """
        # Get the appropriate metrics based on split
        metrics_attr = f"{split.value}_metrics"
        metrics = getattr(self, metrics_attr, None)

        # If no metrics or run_id, skip calculation
        if not metrics or not self.run_id:
            return

        # Load data if not provided
        if x_data is None or y_data is None:
            if self.x_data is None or self.y_data is None:
                return
            x_data = self.x_data[split.value]
            y_data = self.y_data[split.value]

        # If data is empty after retrieval, skip calculation
        if x_data is None or y_data is None:
            return

        # Make predictions and transform outputs
        y_pred = self.predict(x_data)
        y_transformed = self.prepare_output(y_data, is_fit=False)

        # Calculate metric scores
        results = {}
        for metric in metrics:
            score = metric.score(y_transformed, y_pred)
            if not math.isfinite(score):
                logger.warning(
                    "Metric %s returned a non-finite value (%s) for split %s "
                    "(e.g. only one class present in the split). Skipping.",
                    metric.__name__,
                    score,
                    split,
                )
                continue
            results[metric.__name__] = score

        # Save to database
        self._save_metrics(
            split=split,
            level=level,
            results=results,
            log_index=log_index,
            fold_index=fold_index,
            inner_fold_index=inner_fold_index,
        )

        # Report the epoch to whoever is watching, AFTER persisting: the reporter
        # is allowed to raise (Optuna prunes that way), and the metrics of the
        # epoch that triggered the stop should survive it.
        if (
            self._epoch_reporter is not None
            and level is LevelEnum.EPOCH
            and split is SplitEnum.VALIDATION
        ):
            self._epoch_reporter(results, log_index)

    # Create a function similar to calculate_metrics that returns the scores
    # instead of saving them to the database, to be used in the CV evaluation loop
    def compute_metrics(
        self,
        split: SplitEnum = SplitEnum.TEST,
        x_data: "DashAIDataset" = None,
        y_data: "DashAIDataset" = None,
    ) -> Dict[str, float]:
        """Calculate and return metric scores for a given data split.

        Parameters
        ----------
        split : SplitEnum
            The data split to evaluate (TRAIN, VALIDATION,
            or TEST). Defaults to SplitEnum.VALIDATION.
        x_data : DashAIDataset, optional
            Input features. If None, the
            dataset stored in the model for the given split is used.
            Defaults to None.
        y_data : DashAIDataset, optional
            Target labels. If None, the
            labels stored in the model for the given split are used.
            Defaults to None.

        Returns
        -------
        Dict[str, float]
            A dictionary mapping metric names to their computed scores.
        """
        # Get the appropriate metrics based on split
        metrics_attr = f"{split.value}_metrics"
        metrics = getattr(self, metrics_attr, None)

        # If no metrics, return empty dict
        if not metrics:
            return {}

        # Load data if not provided
        if x_data is None or y_data is None:
            if self.x_data is None or self.y_data is None:
                return {}
            x_data = self.x_data[split.value]
            y_data = self.y_data[split.value]

        # If data is empty after retrieval, return empty dict
        if x_data is None or y_data is None:
            return {}

        # Make predictions and transform outputs
        y_pred = self.predict(x_data)
        y_transformed = self.prepare_output(y_data, is_fit=False)

        # Calculate metric scores
        results = {}
        for metric in metrics:
            score = metric.score(y_transformed, y_pred)
            results[metric.__name__] = score

        return results

    def prepare_dataset(
        self, dataset: "DashAIDataset", is_fit: bool = False
    ) -> "DashAIDataset":
        """Hook for model specific preprocessing of input features.

        Override in subclasses that require custom tokenization, encoding,
        or any other input transformation. Must not mutate the input in place.

        Parameters
        ----------
        dataset : DashAIDataset
            The input dataset to preprocess.
        is_fit : bool
            Whether the call is part of a fitting phase.
            Defaults to False.

        Returns
        -------
        DashAIDataset
            The preprocessed dataset ready to be fed into
            the model.
        """
        return dataset

    def predict_prepared(self, features: Any) -> Any:
        """Predict from data that is already in this model's feature space.

        ``predict`` takes a ``DashAIDataset`` with the raw columns and runs
        ``prepare_dataset`` itself. Explainers that perturb the feature matrix
        (SHAP, partial dependence, permutation importance, DiCE) instead hold a
        frame that ``prepare_dataset`` already produced, and must not have it
        prepared a second time. They call this method.

        Subclasses that can consume a feature matrix must override it, and
        should implement ``predict`` as
        ``self.predict_prepared(self.prepare_dataset(x, is_fit=False).to_pandas())``
        so both paths share the same estimator call.

        Parameters
        ----------
        features : pandas.DataFrame or numpy.ndarray
            Feature matrix as returned by ``prepare_dataset(..., is_fit=False)``.
            No further preparation is applied to it.

        Returns
        -------
        Any
            The same kind of output as ``predict``: predicted values for
            regressors, class probabilities for DashAI classifiers.

        Raises
        ------
        NotImplementedError
            If the model cannot consume a raw feature matrix.
        """
        raise NotImplementedError(
            f"{type(self).__name__} does not support prediction from a prepared "
            "feature matrix, so explainers that perturb the model input are not "
            "available for it."
        )

    def predict_proba_prepared(self, features: Any) -> Any:
        """Return class probabilities for data already in the feature space.

        Classification counterpart of ``predict_prepared``, for explainers that
        need the sklearn-native ``predict_proba`` semantics.

        Parameters
        ----------
        features : pandas.DataFrame or numpy.ndarray
            Feature matrix as returned by ``prepare_dataset(..., is_fit=False)``.

        Returns
        -------
        numpy.ndarray
            Array of shape ``(n_samples, n_classes)`` with class probabilities.

        Raises
        ------
        NotImplementedError
            If the model cannot consume a raw feature matrix.
        """
        raise NotImplementedError(
            f"{type(self).__name__} does not support probability prediction from "
            "a prepared feature matrix, so explainers that perturb the model "
            "input are not available for it."
        )

    def prepare_output(
        self, dataset: "DashAIDataset", is_fit: bool = False
    ) -> "DashAIDataset":
        """Hook for model-specific preprocessing of output targets.

        By default, delegates to `prepare_dataset`. Override in subclasses
        that need separate input and output preprocessing logic.

        Parameters
        ----------
        dataset : DashAIDataset
            The output dataset (target labels) to
            preprocess.
        is_fit : bool
            Whether the call is part of a fitting phase.
            Defaults to False.

        Returns
        -------
        DashAIDataset
            The preprocessed output dataset.
        """
        return self.prepare_dataset(dataset, is_fit)
