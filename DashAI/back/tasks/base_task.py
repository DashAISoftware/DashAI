import json
import logging
from collections import defaultdict
from typing import Type

import numpy as np
from datasets import DatasetDict

from DashAI.back.models.classes.getters import filter_by_parent

logger = logging.getLogger(__name__)


class TaskMetaClass(type):
    """Allows each Task to hold an own empty compatible_models list.

    The reason for this is that if compatible_models is declared in BaseTask as a class
    variable, all tasks that extend BaseTask will use the same array of compatible
    models, rendering its use useless.

    The metaclass makes that each class that extends BaseClass has a new
    compatible_models list as its own class variable (and thus, avoids sharing it with
    the others).
    """

    def __new__(cls, name, bases, dct):
        task = super().__new__(cls, name, bases, dct)
        task.compatible_components = defaultdict(lambda: defaultdict(str))
        return task


class BaseTask(metaclass=TaskMetaClass):
    """
    Task is an abstract class for all the Task implemented in the framework.
    Never use this class directly.
    """

    # task name, present in the compatible models
    name: str = ""
    schema: dict = {}

    @classmethod
    def add_compatible_component(
        cls,
        registry_for: Type,
        component: Type,
    ) -> None:
        """Add a model to the task compatible models registry.

        Parameters
        ----------
        model : Model
            Some model that extends the Model class.
        Raises
        ------
        TypeError
            In case that model is not a class.
        TypeError
            In case that model is not a Model subclass.
        """

        if not isinstance(component, type):
            raise TypeError(f"obj should be class, got {component}")

        cls.compatible_components[registry_for.__name__][component.__name__] = component

    @classmethod
    def get_schema(self) -> dict:
        """
        This method load the schema JSON file asocciated to the task.
        """
        try:
            with open(f"DashAI/back/tasks/tasks_schemas/{self.name}.json", "r") as f:
                schema = json.load(f)
            return schema
        except FileNotFoundError:
            logger.exception(
                (
                    f"Could not load the schema for {self.__name__} : File DashAI/back"
                    f"/tasks/tasks_schemas/{self.name}.json not found."
                )
            )
            return {}

    def set_executions(self, model: str, param: dict) -> None:
        """
        This method configures one execution per model in models with the parameters
        in the params[model] dictionary.
        The executions were temporaly save in self.executions.
        """

        def parse_params(model_json, model_params):
            """
            Generate model's parameter dictionary, instantiating recursive
            parameters.
            """
            execution_params = {}
            for json_param in model_json:
                if model_json.get(json_param)["oneOf"][0].get("type") == "class":
                    param_choice = model_params[json_param].pop(
                        "choice"
                    )  # TODO See how to get the user choice
                    param_class = filter_by_parent(
                        model_json.get(json_param)["oneOf"][0].get("parent")
                    ).get(param_choice)
                    param_sub_params = parse_params(
                        param_class.SCHEMA.get("properties"), model_params[json_param]
                    )
                    execution_params[json_param] = param_class(**param_sub_params)
                else:
                    execution_params[json_param] = model_params[json_param]
            return execution_params

        # TODO
        # Remove models from the method signature
        # Generate a Grid to search the best model
        # self.executions: list = []
        # for model, model_params in params.items():
        execution = self.compatible_models[model]
        model_json = execution.SCHEMA.get("properties")
        # TODO use JSON_SCHEMA to check user params
        execution_params = parse_params(model_json, param)
        return execution(**execution_params)

    def run_experiments(self, input_data: dict):
        """
        This method train all the executions in self.executions with the data in
        input_data.
        The input_data dictionary must have train and test keys to perform the training.
        The test results were temporaly save in self.experimentResults.
        """
        # print("EXECUTIONS:")
        # print(self.executions)
        x_train = np.array(input_data["train"]["x"])
        y_train = np.array(input_data["train"]["y"])
        x_test = np.array(input_data["test"]["x"])
        y_test = np.array(input_data["test"]["y"])

        self.categories = []
        for cat in y_train:
            if cat not in self.categories:
                self.categories.append(cat)
        for cat in y_test:
            if cat not in self.categories:
                self.categories.append(cat)

        numeric_y_train = []
        for sample in y_train:
            numeric_y_train.append(self.categories.index(sample))
        numeric_y_test = []
        for sample in y_test:
            numeric_y_test.append(self.categories.index(sample))

        for execution in self.executions:
            execution.fit(x_train, numeric_y_train)

            trainResults = execution.score(x_train, numeric_y_train)
            testResults = execution.score(x_test, numeric_y_test)
            parameters = execution.get_params()
            # executionBytes = execution.save()

            self.experimentResults[execution.MODEL] = {
                "train_results": trainResults,
                "test_results": testResults,
                "parameters": parameters,
                # " executionBytes": executionBytes,
            }

    def get_prediction(self, execution_id, x):
        """Returns the predicted output of x, given by the execution execution_id"""
        cat = self.executions[execution_id].predict(
            self.parse_single_input_from_string(x)
        )
        final_cat = self.map_category(int(cat[0]))
        return final_cat

    def validate_dataset_for_task(self, dataset: DatasetDict):
        for split in dataset.keys():
            schema = self.schema
            allowed_input_types = tuple(schema["inputs_types"])
            allowed_output_types = tuple(schema["outputs_types"])
            inputs_cardinality = schema["inputs_cardinality"]
            outputs_cardinality = schema["outputs_cardinality"]

            # Check input types
            for input_col in dataset[split].inputs_columns:
                input_col_type = dataset[split].features[input_col]
                if not isinstance(input_col_type, allowed_input_types):
                    raise TypeError(
                        f"{input_col_type} is not an allowed type for input columns"
                    )

            # Check output types
            for output_col in dataset[split].outputs_columns:
                output_col_type = dataset[split].features[output_col]
                if not isinstance(output_col_type, allowed_output_types):
                    raise TypeError(
                        f"{output_col_type} is not an allowed type for output columns"
                    )

            # Check input cardinality
            if (
                inputs_cardinality != "n"
                and len(dataset[split].inputs_columns) != inputs_cardinality
            ):
                raise ValueError(
                    f"Input cardinality ({len(dataset[split].inputs_columns)}) does not"
                    f" match task cardinality ({inputs_cardinality})"
                )

            # Check output cardinality
            if (
                outputs_cardinality != "n"
                and len(dataset[split].outputs_columns) != outputs_cardinality
            ):
                raise ValueError(
                    f"Output cardinality ({len(dataset[split].outputs_columns)})"
                    f" does not "
                    f"match task cardinality ({outputs_cardinality})"
                )
