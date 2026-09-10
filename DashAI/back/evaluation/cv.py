from functools import partial

import numpy as np
from kink import di

from DashAI.back.core.enums.metrics import LevelEnum, SplitEnum
from DashAI.back.dependencies.database.models import Metric, Run
from DashAI.back.evaluation.base_evaluation_strategy import BaseEvaluationStrategy
from DashAI.back.splitters.base_splitter import BaseSplitter


class FoldEvaluationStrategy(BaseEvaluationStrategy):
    """Evaluation strategy implementing k-fold cross-validation with optional
    nested CV and HPO.

    This strategy partitions the dataset into k folds and performs k rounds of
    training and evaluation. Each fold is split into a train and a validation
    partition, so the scores obtained by resampling are validation estimates.
    When the session reserved rows, the final model is fitted on everything the
    folds could use and scored once against those reserved rows.

    The strategy handles metric aggregation at multiple levels:
    - FOLD level: Individual metrics from each fold
    - TRIAL level: Metrics during HPO trials
    - LAST/LAST_OUTER: Aggregated metrics (mean and std) for simple/nested CV
    """

    KIND: str = "cv"

    def execute(self, x, y, run: Run, db):
        """Execute k-fold cross-validation with optional nested CV and HPO.

        Trains and evaluates a model using k-fold cross-validation. Optionally performs
        hyperparameter optimization and nested CV to prevent overfitting. Aggregates
        metrics across folds and returns the trained model.

        Parameters
        ----------
        x : list of DatasetDict
            List of fold DatasetDict each containing:
            {"train": X_train, "validation": X_validation}
            The last element is not a fold: it holds every row the folds could
            use as {"train": X_pool, "test": X_test}, where the test partition
            is empty when the session reserved nothing.
        y : list of DatasetDict
            List of fold label DatasetDicts with same structure as x.
        run : Run
            Database run instance containing configuration (nested CV settings, etc.).
        db : Session
            SQLAlchemy database session for persisting metrics and parameters.

        Returns
        -------
        tuple
            (trained_model, plot_paths) where:
            - trained_model : BaseModel - The trained model
            - plot_paths : list[str] - Paths to HPO visualization plot files
        """
        plot_paths = []
        model = self.model

        # STEP 1: Hyperparameter Optimization (if enabled)
        if self.optimizer and self.run_optimizable_parameters:
            # Initialize nested CV if required
            if run.nested:
                try:
                    registry = di["component_registry"]
                    inner_splits = run.nested
                    splitter_name = inner_splits.get("splitter_name", None)

                    # Create inner splitter for nested CV fold generation
                    self.inner_splitter: BaseSplitter = registry[splitter_name][
                        "class"
                    ](inner_splits)
                except Exception as e:
                    raise ValueError(
                        f"Error configuring inner splitter for nested CV: {e}"
                    ) from e

                # Execute nested cross-validation for HPO
                self._report_progress(0.1, "Nested cross-validation")
                self._nested_cv(run.id, model, x, y, db)

            # Perform hyperparameter optimization and update run.parameters
            self._report_progress(0.25, "Hyperparameter optimization")
            model = self._do_hpo(model, x, y, run, db)

            # Generate and serialize HPO visualization plots
            plot_paths = self._generate_hpo_plots(run)

        total_folds = len(x) - 1

        # STEP 2: Main k-fold Cross-Validation Loop
        # Note: Last fold (index len(x)-1) is reserved for final training,
        # not CV evaluation
        for i in range(total_folds):
            self._report_progress(
                0.4 + ((i + 1) / total_folds) * 0.4,
                f"Evaluating fold {i + 1}/{total_folds}",
            )
            x_fold = x[i]
            y_fold = y[i]

            # Set model's internal references to current fold data
            model.x_data = x_fold
            model.y_data = y_fold

            # Train model on fold's training partition
            model.train(x_fold["train"], y_fold["train"])

            # Compute and store metrics for this fold
            if SplitEnum.TRAIN in self.SCORED_SPLITS:
                model.calculate_metrics(
                    split=SplitEnum.TRAIN, level=LevelEnum.FOLD, fold_index=i
                )
            model.calculate_metrics(
                split=SplitEnum.VALIDATION, level=LevelEnum.FOLD, fold_index=i
            )

        # STEP 3: Aggregate metrics across all folds
        # Compute mean and std of fold metrics and store as LAST level metrics
        self._aggregate_fold_metrics(
            run_id=run.id,
            db=db,
            level_to_agg=LevelEnum.FOLD,
            level_to_save=LevelEnum.LAST,
        )

        # STEP 4: Final model training on every row the folds could use, which
        # excludes the rows reserved when the session asked for them.
        self._report_progress(0.85, "Training final model")
        model.x_data = x[-1]
        model.y_data = y[-1]
        model.train(x[-1]["train"], y[-1]["train"])

        # STEP 5: Score the final model once on the reserved rows. No fold and
        # no hyperparameter trial ever saw them, so this is the only estimate
        # that stays honest after a model is picked out of the comparison
        # table. It is a single measurement, hence no standard deviation.
        if len(x[-1]["test"]) > 0:
            self._report_progress(0.90, "Evaluating on the reserved rows")
            model.calculate_metrics(split=SplitEnum.TEST, level=LevelEnum.LAST)

        return model, plot_paths

    def evaluate(self, model, input_dataset, output_dataset, metric, **kwargs):
        """Evaluate model using k-fold cross-validation (used as HPO objective
        function).

        This method implements cross-validation evaluation for hyperparameter
        optimization. It trains on each fold's train partition, scores the fold's
        validation partition and averages the results. When used in nested CV, it
        evaluates on inner folds within a specific outer fold.

        Parameters
        ----------
        model : BaseModel
            The model instance to evaluate (with specific hyperparameters).
        input_dataset : list of DatasetDict
            List of fold data {"train": X_train, "validation": X_validation}.
        output_dataset : list of DatasetDict
            List of fold labels {"train": y_train, "validation": y_validation}.
        metric : Metric
            The metric function to optimize.
        **kwargs
            Additional arguments including:
            - fold_index : int or None
              Inner outer fold index in nested CV (None for simple CV)

        Returns
        -------
        float
            Mean metric value across all k folds (objective value for HPO).

        Note: When fold_index is provided (nested CV inner loop),
        intermediate metrics are NOT being saved (only outer loop metrics are saved).
        """
        # Extract context: fold_index indicates if we're in nested CV inner loop
        # None means simple CV; an integer means nested CV on that outer fold
        fold_index = kwargs.get("fold_index")

        # List to collect the goal metric value from each fold
        folds_results = []

        # Dictionaries to accumulate all metrics across folds for averaging
        train_results = {}
        validation_results = {}

        # Cross-validation loop
        # Iterate through k-1 folds (last fold is the complete dataset)
        # This loop represents either:
        # - Main CV loop (if fold_index is None)
        # - Inner CV loop within outer fold i (if fold_index is set)
        for i in range(len(input_dataset) - 1):
            x_fold = input_dataset[i]
            y_fold = output_dataset[i]

            # Set model's internal data references for this fold
            model.x_data = x_fold
            model.y_data = y_fold

            # Train model on this fold's training partition
            model.train(x_fold["train"], y_fold["train"])

            # Compute metrics on both training and validation sets
            train_scores = (
                model.compute_metrics(split=SplitEnum.TRAIN)
                if SplitEnum.TRAIN in self.SCORED_SPLITS
                else {}
            )
            validation_scores = model.compute_metrics(split=SplitEnum.VALIDATION)

            # Collect the goal metric value from this fold
            folds_results.append(validation_scores[metric.__name__])

            # Accumulate all metrics only if NOT in nested CV inner loop
            if fold_index is None:
                for results, scores in [
                    (train_results, train_scores),
                    (validation_results, validation_scores),
                ]:
                    for metric_name, value in scores.items():
                        if metric_name not in results:
                            results[metric_name] = []
                        results[metric_name].append(value)

        # Save intermediate metrics (simple CV only)
        if fold_index is None:
            # Compute average metrics across all folds
            averaged_train_results = {
                metric: np.mean(values) for metric, values in train_results.items()
            }
            averaged_validation_results = {
                metric: np.mean(values) for metric, values in validation_results.items()
            }

            # Persist averaged metrics as TRIAL level (intermediate HPO result)
            if SplitEnum.TRAIN in self.SCORED_SPLITS:
                model._save_metrics(
                    results=averaged_train_results,
                    split=SplitEnum.TRAIN,
                    level=LevelEnum.TRIAL,
                )
            model._save_metrics(
                results=averaged_validation_results,
                split=SplitEnum.VALIDATION,
                level=LevelEnum.TRIAL,
            )

        # Return the mean of the goal metric across folds
        # This is the objective value used by the optimizer
        return np.mean(folds_results)

    def _nested_cv(self, run_id, model, input_dataset, output_dataset, db):
        """Execute nested cross-validation with inner HPO loop.

        Nested CV implements a two-level validation scheme to prevent overfitting during
        hyperparameter optimization and give an unbiased estimate of model performance.
        - Outer loop: Standard k-fold CV for unbiased final performance estimation
        - Inner loop: Separate CV fold within each outer fold for HPO

        This prevents "information leakage" where the data used to score a fold also
        influences hyperparameter selection, which would overestimate true
        generalization performance.

        Parameters
        ----------
        run_id : int
            The database run ID for metric storage.
        model : BaseModel
            The model instance to optimize and evaluate.
        input_dataset : list of DatasetDict
            List of outer fold data
            {"train": X_train, "validation": X_validation}.
        output_dataset : list of DatasetDict
            List of outer fold labels
            {"train": y_train, "validation": y_validation}.
        db : Session
            SQLAlchemy database session for persisting aggregated metrics.
        """
        # Nested CV Outer Loop
        # For each outer fold, optimize hyperparameters on inner folds
        for i in range(len(input_dataset) - 1):
            x_outer = input_dataset[i]
            y_outer = output_dataset[i]

            # Create inner folds from outer fold's training data
            # This ensures HPO validation data is independent of outer test fold
            inner_x, inner_y, _ = self.inner_splitter.split(
                x_outer["train"], y_outer["train"]
            )

            # Create evaluation strategy for this outer fold
            # Passes fold_index so evaluate() knows it's in nested CV context
            strategy_with_context = partial(self.evaluate, fold_index=i)

            # INNER LOOP: Optimize hyperparameters using inner CV
            # The optimizer will iteratively:
            # - Generate hyperparameter candidates
            # - Train models on inner fold combinations
            # - Evaluate using inner CV (calls strategy_with_context)
            # - Select hyperparameters with best inner CV performance
            self.optimizer.optimize(
                model,
                inner_x,
                inner_y,
                self.run_optimizable_parameters,
                self.goal_metric,
                strategy=strategy_with_context,
            )
            outer_model = self.optimizer.get_model()

            # Set model's data references for outer fold evaluation
            outer_model.x_data = x_outer
            outer_model.y_data = y_outer

            # Train model on outer fold's training data with optimized hyperparameters
            outer_model.train(x_outer["train"], y_outer["train"])

            # Evaluate on outer fold's test data (this is OUTER_FOLD level metric)
            outer_model.calculate_metrics(
                split=SplitEnum.VALIDATION, level=LevelEnum.OUTER_FOLD, fold_index=i
            )
            if SplitEnum.TRAIN in self.SCORED_SPLITS:
                outer_model.calculate_metrics(
                    split=SplitEnum.TRAIN, level=LevelEnum.OUTER_FOLD, fold_index=i
                )

        # Aggregate outer fold metrics
        # Compute mean and std of OUTER_FOLD metrics and store as LAST_OUTER level
        self._aggregate_fold_metrics(
            run_id=run_id,
            db=db,
            level_to_agg=LevelEnum.OUTER_FOLD,
            level_to_save=LevelEnum.LAST_OUTER,
        )

    def _aggregate_fold_metrics(
        self,
        run_id: int,
        db,
        level_to_agg=LevelEnum.FOLD,
        level_to_save=LevelEnum.LAST,
    ):
        """Aggregate and average fold metrics across cross-validation folds.

        This method computes the mean and standard deviation of metrics collected
        at the fold level and stores the aggregated results at a higher level.
        This is used to provide summary statistics for model performance.

        Typical usage patterns:
        - Aggregate FOLD metrics -> store as LAST (simple CV summary)
        - Aggregate OUTER_FOLD metrics -> store as LAST_OUTER (nested CV summary)

        Parameters
        ----------
        run_id : int
            The database run ID to aggregate metrics for.
        db : Session
            SQLAlchemy database session for querying and persisting metrics.
        level_to_agg : LevelEnum, optional
            The source metric level to aggregate. Default: FOLD.
        level_to_save : LevelEnum, optional
            The destination level for aggregated metrics. Default: LAST.
        """
        # Query all metrics with level=level_to_agg for this run
        fold_metrics = (
            db.query(Metric)
            .filter(Metric.run_id == run_id, Metric.level == level_to_agg)
            .all()
        )

        # If no metrics found, nothing to aggregate
        if not fold_metrics:
            return

        # Group metrics by (split, name) for aggregation
        metrics_by_split_name = {}
        for metric in fold_metrics:
            key = (metric.split, metric.name)
            if key not in metrics_by_split_name:
                metrics_by_split_name[key] = []
            metrics_by_split_name[key].append(metric.value)

        # Aggregate and persist metrics
        for (split, name), values in metrics_by_split_name.items():
            # Compute aggregation statistics
            avg_value = np.mean(values)
            std_value = np.std(values) if len(values) > 1 else 0.0

            # Check if aggregated metric already exists for this split/name/run
            existing = (
                db.query(Metric)
                .filter_by(run_id=run_id, split=split, level=level_to_save, name=name)
                .first()
            )

            if existing:
                # Update existing metric with aggregated values
                existing.value = avg_value
                existing.std_value = std_value
            else:
                # Create new aggregated metric
                db.add(
                    Metric(
                        run_id=run_id,
                        split=split,
                        level=level_to_save,
                        name=name,
                        value=avg_value,
                        std_value=std_value,
                        step=0,
                    )
                )

        # Persist aggregated metrics to database
        db.commit()


class CrossValidationEvaluationStrategy(FoldEvaluationStrategy):
    """Score a model across folds, recording train and validation for each.

    The ordinary cross-validation evaluation. Not offered for
    ``ForecastingTask``, whose folds have no in-sample score to report;
    ``ForecastingCrossValidationEvaluationStrategy`` handles that.
    """

    COMPATIBLE_COMPONENTS = [
        "TabularClassificationTask",
        "TextClassificationTask",
        "ImageClassificationTask",
        "TranslationTask",
        "RegressionTask",
    ]
