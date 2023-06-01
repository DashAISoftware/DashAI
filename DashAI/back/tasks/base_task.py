import json
import logging
from abc import abstractmethod
from collections import defaultdict
from typing import Type

from datasets import DatasetDict

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

    def validate_dataset_for_task(self, dataset: DatasetDict, dataset_name: str):
        """Validate a dataset for the current task.

        Parameters
        ----------
        dataset : DatasetDict
            Dataset to be validated
        dataset_name : str
            Dataset name
        """
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
                        f"Error in split {split} of dataset {dataset_name}. "
                        f"{input_col_type} is not an allowed type for input columns."
                    )

            # Check output types
            for output_col in dataset[split].outputs_columns:
                output_col_type = dataset[split].features[output_col]
                if not isinstance(output_col_type, allowed_output_types):
                    raise TypeError(
                        f"Error in split {split} of dataset {dataset_name}. "
                        f"{output_col_type} is not an allowed type for output columns. "
                    )

            # Check input cardinality
            if (
                inputs_cardinality != "n"
                and len(dataset[split].inputs_columns) != inputs_cardinality
            ):
                raise ValueError(
                    f"Error in split {split} of dataset {dataset_name}. "
                    f"Input cardinality ({len(dataset[split].inputs_columns)}) does not"
                    f" match task cardinality ({inputs_cardinality})"
                )

            # Check output cardinality
            if (
                outputs_cardinality != "n"
                and len(dataset[split].outputs_columns) != outputs_cardinality
            ):
                raise ValueError(
                    f"Error in split {split} of dataset {dataset_name}. "
                    f"Output cardinality ({len(dataset[split].outputs_columns)})"
                    f" does not "
                    f"match task cardinality ({outputs_cardinality})"
                )

    @abstractmethod
    def prepare_for_task(self, dataset: DatasetDict):
        """Change the column types to suit the task requirements.
        A copy of the dataset is created.

        Parameters
        ----------
        dataset : DatasetDict
            Dataset to be changed

        Returns
        -------
        DatasetDict
            Dataset with the new types
        """
        raise NotImplementedError
