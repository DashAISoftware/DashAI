import optuna

from DashAI.back.core.schema_fields import (
    BaseSchema,
    enum_field,
    int_field,
    schema_field,
)
from DashAI.back.optimizers.base_optimizer import BaseOptimizer


class OptunaSchema(BaseSchema):
    n_trials: schema_field(
        int_field(gt=0),
        placeholder=10,
        description="The parameter 'n_trials' is the quantity of trials"
        "per study. It must be of type positive integer.",
    )  # type: ignore
    sampler: schema_field(
        enum_field(enum=["TPESampler", "CmaEsSampler"]),
        placeholder="TPESampler",
        description="Coefficient for 'rbf', 'poly' and 'sigmoid' kernels"
        ". Must be in string format and can be 'scale' or 'auto'.",
    )  # type: ignore
    pruner: schema_field(
        enum_field(enum=["MedianPruner", "None"]),
        placeholder="None",
        description="Coefficient for 'rbf', 'poly' and 'sigmoid' kernels"
        ". Must be in string format and can be 'scale' or 'auto'.",
    )  # type: ignore
    metric: schema_field(
        enum_field(enum=["Accuracy", "F1Score"]),
        placeholder="Accuracy",
        description="Coefficient for 'rbf', 'poly' and 'sigmoid' kernels."
        "Must be in string format and can be 'scale' or 'auto'.",
    )  # type: ignore


class OptunaOptimizer(BaseOptimizer):
    SCHEMA = OptunaSchema

    COMPATIBLE_COMPONENTS = [
        "TabularClassificationTask",
        "TextClassificationTask",
        "TranslationTask",
    ]

    def __init__(self, n_trials=None, sampler=None, pruner=None, metric=None):
        self.n_trials = n_trials
        self.sampler = getattr(optuna.samplers, sampler)
        self.pruner = pruner
        self.metric = metric

    def optimize(self, model, input_dataset, output_dataset, parameters, task):
        """
        Optimization process

        Args:
            model (class): class for the model from the current experiment
            dataset (dict): dict with the data to train and validation
            parameters (dict): dict with the information to create the search space
            metric (class): class for the metric to optimize

        Returns
        -------
            best_model: Object from the class model with the best hyperparameters found.
        """
        self.model = model
        self.input_dataset = input_dataset
        self.output_dataset = output_dataset
        self.parameters = parameters

        if self.metric["name"] in ["Accuracy", "F1", "Precision", "Recall"]:
            study = optuna.create_study(
                direction="maximize", sampler=self.sampler(), pruner=self.pruner
            )
        else:
            study = optuna.create_study(
                direction="minimize", sampler=self.sampler(), pruner=self.pruner
            )

        self.metric = self.metric["class"]

        if task == "TextClassificationTask":

            def objective(trial):
                vectorizer_trial = self.model.vectorizer
                classifier_trial = self.model.classifier
                for hyperparameter, values in self.parameters.items():
                    value = trial.suggest_int(hyperparameter, values[0], values[-1])
                    setattr(classifier_trial, hyperparameter, value)

                model_trial = self.model
                model_trial.vectorizer = vectorizer_trial
                model_trial.classifier = classifier_trial
                model_trial.fit(
                    self.input_dataset["train"], self.output_dataset["train"]
                )
                y_pred = model_trial.predict(input_dataset["validation"])
                score = self.metric.score(output_dataset["validation"], y_pred)

                return score

        else:

            def objective(trial):
                model_trial = self.model
                for hyperparameter, values in self.parameters.items():
                    value = trial.suggest_int(hyperparameter, values[0], values[-1])
                    setattr(model_trial, hyperparameter, value)

                model_trial.fit(
                    self.input_dataset["train"], self.output_dataset["train"]
                )
                y_pred = model_trial.predict(input_dataset["validation"])
                score = self.metric.score(output_dataset["validation"], y_pred)

                return score

        study.optimize(objective, n_trials=self.n_trials)

        best_params = study.best_params
        best_model = self.model
        for hyperparameter, value in best_params.items():
            setattr(best_model, hyperparameter, value)
        best_model.fit(self.input_dataset["train"], self.output_dataset["train"])
        self.model = best_model

    def get_model(self):
        return self.model
