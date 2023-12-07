from abc import abstractmethod
from typing import Any, Dict, Final

from datasets import DatasetDict


class BaseTask:
    """Base class for DashAI compatible tasks."""

    TYPE: Final[str] = "Task"

    @property
    @abstractmethod
    def schema(self) -> Dict[str, Any]:
        raise NotImplementedError

    def get_metadata(self) -> Dict[str, Any]:
        """Get metadata values for the current task

        Returns:
            Dict[str, Any]: Dictionary with the metadata
        """
        metadata = self.metadata

        # Extract class names
        inputs_types = [i.__name__ for i in metadata["inputs_types"]]
        outputs_types = [i.__name__ for i in metadata["outputs_types"]]

        parsed_metadata: dict = {
            "inputs_types": inputs_types,
            "outputs_types": outputs_types,
            "inputs_cardinality": metadata["inputs_cadinality"],
            "outputs_cardinality": metadata["outputs_cadinality"],
        }
        return parsed_metadata

    def validate_dataset_for_task(
        self, dataset: DatasetDict, dataset_name: str
    ) -> None:
        """Validate a dataset for the current task.

        Parameters
        ----------
        dataset : DatasetDict
            Dataset to be validated
        dataset_name : str
            Dataset name
        """
        for split in dataset:
            metadata = self.metadata
            allowed_input_types = tuple(metadata["inputs_types"])
            allowed_output_types = tuple(metadata["outputs_types"])
            inputs_cardinality = metadata["inputs_cardinality"]
            outputs_cardinality = metadata["outputs_cardinality"]

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
    def prepare_for_task(self, dataset: DatasetDict) -> DatasetDict:
        """Change column types to suit the task requirements.

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
