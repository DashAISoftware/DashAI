from abc import abstractmethod

from Models.classes.getters import filter_by_parent
from TaskLib.task.taskMetaclass import TaskMetaclass


class Task(metaclass=TaskMetaclass):
    """
    Task is an abstract class for all the Task implemented in the framework.
    Never use this class directly.
    """

    # task name, present in the compatible models
    NAME: str = ""
    compatible_models: list = []
    executions = []
    experimentResults = []

    def __init__(self):
        self.executions: list = []
        self.set_compatible_models()

    def set_compatible_models(self) -> None:

        task_name = self.NAME if self.NAME else Exception("Need to specify task name")
        # models_dict = filter_by_parent("Model")
        model_class_name = f"{task_name[:-4]}Model"
        models_dict = filter_by_parent(model_class_name)
        # for model in models_dict.keys():
        #     if models_dict[model].TASK_COMPATIBILITY == self.NAME:
        #      self.compatible_models.append(model)
        self.compatible_models = models_dict
        return

    def get_compatible_models(self) -> list:
        return self.compatible_models

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
        self.executions.append(execution(**execution_params))

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
        print("EXECUTIONS:")
        print(self.executions)

        formated_data = self.parse_input(input_data)

        self.experimentResults = {}

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
    def parse_input(self, input_data):
        pass
