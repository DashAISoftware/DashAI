import importlib

from hyperopt import fmin, hp, rand, tpe  # noqa: F401

from DashAI.back.core.schema_fields import (
    BaseSchema,
    enum_field,
    int_field,
    schema_field,
)
from DashAI.back.optimizers.base_optimizer import BaseOptimizer


class HyperOptSchema(BaseSchema):
    max_evals: schema_field(
        int_field(gt=0),
        placeholder=10,
        description="The parameter 'n_trials' is the quantity of trials"
        "per study. It must be of type positive integer.",
    )  # type: ignore
    sampler: schema_field(
        enum_field(enum=["tpe", "rand"]),
        placeholder="tpe",
        description="Coefficient for 'rbf', 'poly' and 'sigmoid' kernels"
        ". Must be in string format and can be 'scale' or 'auto'.",
    )  # type: ignore
    metric: schema_field(
        enum_field(enum=["Accuracy", "F1Score"]),
        placeholder="Accuracy",
        description="Coefficient for 'rbf', 'poly' and 'sigmoid' kernels."
        "Must be in string format and can be 'scale' or 'auto'.",
    )  # type: ignore


class HyperOptOptimizer(BaseOptimizer):
    SCHEMA = HyperOptSchema

    COMPATIBLE_COMPONENTS = [
        "TabularClassificationTask",
        "TextClassificationTask",
        "TranslationTask",
    ]

    def __init__(self, max_evals=None, sampler=None, metric=None):
        self.max_evals = max_evals
        self.sampler = importlib.import_module(f"hyperopt.{sampler}").suggest
        self.metric = metric["class"]

    def search_space(self, hyperparams_data):
        """
        Configure the search space.

        Args:
            hyperparams_data (dict[str, any]): Dict with the range values
            for the possible search space

        Returns
        -------
            search_space: Dict with the information for the search space .
        """
        search_space = {}

        for hyperparameter, values in hyperparams_data.items():
            search_space[hyperparameter] = hp.quniform(
                hyperparameter, values[0], values[1], 1
            )
        return search_space

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
        search_space = self.search_space(self.parameters)

        if task == "TextClassificationTask":

            def objective(params):
                model_eval = self.model
                model_eval.fit(
                    self.input_dataset["train"], self.output_dataset["train"]
                )
                y_pred = model_eval.predict(input_dataset["validation"])
                score = -1 * self.metric.score(output_dataset["validation"], y_pred)
                return score

        else:

            def objective(params):
                model_eval = self.model
                model_eval.fit(
                    self.input_dataset["train"], self.output_dataset["train"]
                )
                y_pred = model_eval.predict(input_dataset["validation"])
                score = -1 * self.metric.score(output_dataset["validation"], y_pred)
                return score

        best_params = fmin(
            fn=objective,
            space=search_space,
            algo=self.sampler,
            max_evals=self.max_evals,
        )

        best_model = self.model
        for hyperparameter, value in best_params.items():
            setattr(best_model, hyperparameter, value.astype(int))

        best_model.fit(self.input_dataset["train"], self.output_dataset["train"])

        self.model = best_model

    def get_model(self):
        return self.model
