from DashAI.back.core.enums.metrics import LevelEnum, SplitEnum
from DashAI.back.dependencies.database.models import Metric, Run
from DashAI.back.evaluation.base_evaluation_strategy import BaseEvaluationStrategy


class SinglePartitionEvaluationStrategy(BaseEvaluationStrategy):
    """Evaluation strategy implementing holdout (train/validation/test split)
    validation.

    This strategy divides the dataset into three mutually exclusive partitions:
    training, validation, and test. The training set is used for model training,
    the validation set for HPO, and the test set for final evaluation.

    The strategy handles metric aggregation at multiple levels:
    - TRIAL level: Metrics during HPO trials on validation set
    - LAST level: Final metrics computed on all three partitions after training
    """

    KIND: str = "holdout"

    def execute(self, x, y, run: Run, db):
        """Execute holdout validation: train on training set, optimize with validation,
        evaluate on test.

        Trains a model on the training partition and optionally performs hyperparameter
        optimization using the validation set. Finally evaluates the trained model on
        all three partitions (train, validation, test) and returns the model with plots.

        Parameters
        ----------
        x : DatasetDict
            DatasetDict with data partitions:
            {"train": X_train, "validation": X_val, "test": X_test}
        y : DatasetDict
            DatasetDict with label partitions:
            {"train": y_train, "validation": y_val, "test": y_test}
        run : Run
            Database run instance for storing results and configuration.
        db : Session
            SQLAlchemy database session for persisting metrics.

        Returns
        -------
        tuple
            (trained_model, plot_paths) where:
            - trained_model : BaseModel - The trained model
            - plot_paths : list[str] - Paths to HPO visualization plot files
        """
        plot_paths = []
        model = self.model

        # set the data used for model training and evaluation
        model.x_data = x
        model.y_data = y

        # Execute HPO if optimizer and there are parameters to optimize
        if self.optimizer and self.run_optimizable_parameters:
            self._report_progress(0.2, "Hyperparameter optimization")
            model = self._do_hpo(model, x, y, run, db)
            plot_paths = self._generate_hpo_plots(run)

        # Train the model with the provided data and return it
        self._report_progress(0.5, "Training")
        self._fit_final_model(model, x, y)

        # Calculate metrics at the end of training if not done already
        self._report_progress(0.85, "Computing metrics")
        for split in self.SCORED_SPLITS:
            self._calculate_metrics_if_missing(model, run, db, split)

        return model, plot_paths

    def _fit_final_model(self, model, x, y):
        """Fit the model that gets kept.

        Separate from the trial fits so a strategy can differ on what the
        kept model is allowed to learn from, which is the one thing
        forecasting needs to change here.

        Parameters
        ----------
        model : BaseModel
            The model to fit.
        x : DatasetDict
            Input partitions.
        y : DatasetDict
            Target partitions.
        """
        model.train(x["train"], y["train"], x["validation"], y["validation"])

    def _calculate_metrics_if_missing(self, model, run: Run, db, split: SplitEnum):
        """Compute and persist LAST-level metrics for a split, unless already saved.

        Parameters
        ----------
        model : BaseModel
            The trained model to compute metrics on.
        run : Run
            Database run instance the metrics belong to.
        db : Session
            SQLAlchemy database session used to check for existing metrics.
        split : SplitEnum
            The data split to compute metrics for.
        """
        existing_metric = (
            db.query(Metric)
            .filter_by(run_id=run.id, split=split, level=LevelEnum.LAST)
            .first()
        )
        if not existing_metric:
            model.calculate_metrics(split=split, level=LevelEnum.LAST)

    def evaluate(self, model, input_dataset, output_dataset, metric):
        """Evaluate model on validation set during HPO trials.

        Trains the model on the training set and computes the metric on the validation
        set. Used as the objective function during hyperparameter optimization.

        Parameters
        ----------
        model : BaseModel
            The model instance to evaluate with specific hyperparameters.
        input_dataset : DatasetDict
            DatasetDict with data partitions
            {"train": X_train, "validation": X_val, "test": X_test}.
        output_dataset : DatasetDict
            DatasetDict with label partitions
            {"train": y_train, "validation": y_val, "test": y_test}.
        metric : Metric
            The metric function to compute on predictions.

        Returns
        -------
        float
            The metric score value for this hyperparameter combination.
        """
        # Validation data is passed on purpose. Without it the epoch loops
        # skip `calculate_metrics(split=VALIDATION, level=EPOCH)` entirely —
        # they guard it behind `if x_validation is not None` — so during
        # optimization the per-epoch validation score was never computed.
        #
        # That is the deeper reason pruning could not work here: the number a
        # pruner needs to decide did not exist, independently of whether the
        # pruner itself was an instance or a string.
        model.train(
            input_dataset["train"],
            output_dataset["train"],
            input_dataset["validation"],
            output_dataset["validation"],
        )

        # Evaluate the model on the validation set
        y_pred = model.predict(input_dataset["validation"])

        output_dataset_transformed = model.prepare_output(
            output_dataset["validation"], is_fit=False
        )

        # Calculate metric for train and validation data each trial.
        if SplitEnum.TRAIN in self.SCORED_SPLITS:
            model.calculate_metrics(split=SplitEnum.TRAIN, level=LevelEnum.TRIAL)
        model.calculate_metrics(split=SplitEnum.VALIDATION, level=LevelEnum.TRIAL)

        # Compute the objective metric score on the validation set
        score = metric.score(output_dataset_transformed, y_pred)

        return score


class HoldoutEvaluationStrategy(SinglePartitionEvaluationStrategy):
    """Split once into train, validation and test, and score all three.

    The ordinary holdout evaluation. Not offered for ``ForecastingTask``:
    scoring the training partition of a forecaster means predicting on dates
    it was fitted on, which is a fit statistic rather than a forecast and does
    not belong in the same results table as one.
    ``ForecastingHoldoutEvaluationStrategy`` records validation and test only.

    The final fit is the same in both: the kept model is fitted on the training
    partition alone, so it is the model the recorded metrics describe.
    """

    COMPATIBLE_COMPONENTS = [
        "TabularClassificationTask",
        "TextClassificationTask",
        "ImageClassificationTask",
        "TranslationTask",
        "RegressionTask",
    ]
