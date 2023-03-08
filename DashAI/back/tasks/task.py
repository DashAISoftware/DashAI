import logging
from abc import abstractmethod

import joblib

from DashAI.back.models.classes.getters import filter_by_parent
from DashAI.back.tasks.task_metaclass import TaskMetaclass

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)


class Task(metaclass=TaskMetaclass):
    """
    Task is an abstract class for all the Task implemented in the framework.
    Never use this class directly.
    """

    NAME: str = ""
    compatible_models: list = []
    executions_id = []
    executions = []

    def __init__(self):
        self.executions: list = []
        self.set_compatible_models()

    def save(self, filename) -> None:
        joblib.dump(self, filename)

    @staticmethod
    def load(filename):
        return joblib.load(filename)

    def set_compatible_models(self) -> None:
        # TODO do not use the name of the task, just look for
        # models that have the task into its comptaible task.
        task_name = self.NAME if self.NAME else Exception("Need specify task name")
        model_class_name = f"{task_name[:-4]}Model"
        models_dict = filter_by_parent(model_class_name)
        self.compatible_models = models_dict
        return

    def set_executions(self, model: str, param: dict) -> None:
        """
        This method configures one execution per model in models with the
        parameters in the params[model] dictionary.
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
                    try:
                        execution_params[json_param] = model_params[json_param]
                    except KeyError:
                        pass
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

    def parse_single_input_from_string(self, x: str):
        return x

    def get_prediction(self, execution_id, x):
        """Returns the predicted output of x, given by the execution execution_id"""
        pred = self.executions[execution_id].predict(
            self.parse_single_input_from_string(x)
        )
        return pred

    def run_experiments(self, input_data: dict):
        """
        This method train all the executions in self.executions with the data in
        input_data.
        The input_data dictionary must have train and test keys to perform the training.
        The test results were temporaly save in self.experimentResults.
        """
        log.debug("EXECUTIONS:")
        log.debug(self.executions)

        formated_data = self.parse_input(input_data)

        for execution in self.executions:
            execution.fit(formated_data["train"]["x"], formated_data["train"]["y"])
            trainResults = execution.score(
                formated_data["train"]["x"], formated_data["train"]["y"]
            )
            testResults = execution.score(
                formated_data["test"]["x"], formated_data["test"]["y"]
            )
            parameters = execution.get_params()

            self.experimentResults[execution.MODEL] = {
                "train_results": trainResults,
                "test_results": testResults,
                "parameters": parameters,
            }

    @abstractmethod
    def validate_dataset(self, dataset, class_column):
        raise NotImplementedError

    @abstractmethod
    def parse_input(self, input_data):
        pass  # useless (work with old dashAI json format)
