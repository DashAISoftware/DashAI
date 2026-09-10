import os
import pickle
from abc import ABCMeta, abstractmethod
from typing import Callable, Final, List, Optional

from kink import di

from DashAI.back.core.artifacts import normalize_artifacts
from DashAI.back.core.enums.metrics import SplitEnum
from DashAI.back.dependencies.database.models import Run
from DashAI.back.models.base_model import BaseModel
from DashAI.back.models.model_factory import ModelFactory
from DashAI.back.optimizers.base_optimizer import BaseOptimizer


class BaseEvaluationStrategy(metaclass=ABCMeta):
    """Abstract base class defining the interface for model evaluation strategies.

    Concrete implementations (e.g., CrossValidationEvaluationStrategy,
    HoldoutEvaluationStrategy) inherit from this class and provide specific
    strategies for model evaluation.
    """

    TYPE: Final[str] = "EvaluationStrategy"

    KIND: str = "holdout"
    SCORED_SPLITS: tuple = (SplitEnum.TRAIN, SplitEnum.VALIDATION, SplitEnum.TEST)

    FINAL_FIT_PARTITIONS: tuple = ("train",)

    @classmethod
    def get_metadata(cls) -> dict:
        """Describe the strategy for the frontend.

        Returns
        -------
        dict
            Mapping with ``kind``, which says whether this strategy splits the
            dataset once or into folds, and ``scored_splits``, the partitions
            it writes metrics for. A screen that offers one control per
            partition reads the latter instead of assuming all three exist:
            a forecasting strategy scores no training partition, so asking it
            for train metrics finds nothing.
        """
        return {
            "kind": cls.KIND,
            "scored_splits": [split.value for split in cls.SCORED_SPLITS],
        }

    def __init__(
        self,
        factory: ModelFactory,
        optimizer: BaseOptimizer,
        goal_metric,
        **kwargs,
    ):
        """Initialize the evaluation strategy with model and optimization configuration.

        Parameters
        ----------
        factory : ModelFactory
            Factory owning the model to be trained/evaluated and the
            hyperparameters that are eligible for optimization.
        optimizer : BaseOptimizer
            The hyperparameter optimizer instance. Can be None if no HPO is needed.
        goal_metric : dict (obtained from Metric component registry)
            The target metric to optimize during hyperparameter search.
        **kwargs
            Additional keyword arguments passed from subclasses (ignored).
        """
        self.factory: ModelFactory = factory
        self.model: BaseModel = factory.model
        self.run_optimizable_parameters = factory.optimizable_parameters
        self.optimizer: BaseOptimizer = optimizer
        self.goal_metric = goal_metric
        self._progress_reporter: Optional[
            Callable[[Optional[float], Optional[str]], None]
        ] = None

    def set_progress_reporter(
        self,
        progress_reporter: Optional[Callable[[Optional[float], Optional[str]], None]],
    ) -> None:
        """Register a callback that will receive progress updates."""
        self._progress_reporter = progress_reporter

    def _report_progress(
        self, fraction: Optional[float], message: Optional[str] = None
    ):
        """Emit progress updates when a reporter has been registered."""
        if self._progress_reporter is not None:
            self._progress_reporter(fraction, message)

    @abstractmethod
    def execute(self, x, y, run: Run, db):
        """Execute the evaluation strategy on the provided data.

        This is the main entry point for the evaluation process. Subclasses implement
        strategy-specific logic for:
        - Model training across folds/splits
        - Metric computation and persistence
        - HPO execution and result handling

        Parameters
        ----------
        x : DatasetDict or list of DastasetDict
            Input features. Structure depends on the evaluation strategy:
            - For holdout: DatasetDict with train/validation/test splits
            - For CV: List of DatasetDicts, one per fold with train/test splits
        y : dict or list
            Target labels. Same structure as x.
        run : Run
            Database model representing the current experiment run.
        db : Session
            SQLAlchemy database session for persisting results.

        Returns
        -------
        tuple
            (trained_model, plot_paths) where:
            - trained_model : BaseModel - The trained model after evaluation
            - plot_paths : list[str] - Paths to generated HPO visualization files
        """
        raise NotImplementedError("Subclasses must implement this method")

    @abstractmethod
    def evaluate(self, model: BaseModel, x, y, metric):
        """Evaluate the model on the given data and return the score.

        This method is called during hyperparameter optimization to compute
        the objective function value for a given set of hyperparameters.
        Different strategies may compute metrics differently (e.g., across CV folds
        or on a validation split).

        Parameters
        ----------
        model : BaseModel
            The model instance to evaluate.
        x : DatasetDict or list of DastasetDict
            Input features for evaluation (structure depends on strategy).
        y : DatasetDict or list of DastasetDict
            Target labels for evaluation (structure depends on strategy).
        metric : Metric
            The metric instance to compute.

        Returns
        -------
        float
            The computed metric value used as the optimization objective.
        """
        raise NotImplementedError("Subclasses must implement this method")

    def _do_hpo(self, model: BaseModel, x, y, run: Run, db):
        """Execute hyperparameter optimization using the configured optimizer.

        The optimizer uses the self.evaluate method as the objective function,
        allowing each strategy to define its own evaluation logic.

        Parameters
        ----------
        model : BaseModel
            The model instance to optimize.
        x : DatasetDict or list of DatasetDict
            Training input features (structure varies by strategy).
        y : DatasetDict or list of DatasetDict
            Training target labels (structure varies by strategy).
        run : Run
            Database run instance to update with optimized parameters.
        db : Session
            SQLAlchemy database session for transactions.

        Returns
        -------
        BaseModel
            The model with the best hyperparameters found during optimization.
        """
        from sqlalchemy.orm.attributes import flag_modified

        # Execute hyperparameter optimization and get best model with parameters
        self.optimizer.optimize(
            model,
            x,
            y,
            self.run_optimizable_parameters,
            self.goal_metric,
            strategy=self.evaluate,
        )
        model = self.optimizer.get_model()
        best_params = self.optimizer.get_best_params()

        # Update the run's parameters with the optimized hyperparameters
        old_parameters = run.parameters.copy()
        updated_parameters = self.factory.update_parameters(old_parameters, best_params)

        # Persist the updated parameters to the database
        run.parameters = updated_parameters
        flag_modified(run, "parameters")
        db.commit()

        return model

    def _generate_hpo_plots(self, run: Run) -> List[str]:
        """Generate and pickle the hyperparameter optimization plots to disk.

        Shared by every evaluation strategy that runs HPO, so the plot
        generation logic only needs to be maintained in one place.

        Parameters
        ----------
        run : Run
            The run the plots belong to (used for the plot filenames).

        Returns
        -------
        list[str]
            Paths to the pickled plot files, in the order produced by the
            optimizer.
        """
        config = di["config"]
        plot_paths: List[str] = []

        # Retrieve optimization trial data from the optimizer
        trials = self.optimizer.get_trials_values()

        # Generate plot visualizations from the trial data
        # Plots typically show parameter importance, optimization history, etc.
        plot_filenames, plots = self.optimizer.create_plots(
            trials,
            run.id,
            n_params=len(self.run_optimizable_parameters),
            goal_metric=self.goal_metric,
        )

        # Convert plots to serializable format (handles special objects, arrays, etc.)
        normalized_plots = normalize_artifacts(plots)

        # Serialize and persist each plot to disk
        for filename, plot in zip(plot_filenames, normalized_plots, strict=False):
            plot_path = os.path.join(config["RUNS_PATH"], filename)
            # Serialize the plot object using pickle and write to disk
            with open(plot_path, "wb") as file:
                pickle.dump(plot, file)
                plot_paths.append(plot_path)

        return plot_paths
