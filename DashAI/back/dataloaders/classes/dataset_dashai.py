import json
import os
from typing import Dict, List

from datasets import ClassLabel, Dataset, Value, load_from_disk


class DatasetDashAI(Dataset):
    def __init__(
        self,
        table,
        inputs_columns: List[str],
        outputs_columns: List[str],
        *args,
        **kwargs,
    ):
        """DashAI wrapper for Huggingface datasets with extra metadata."""
        super().__init__(table, *args, **kwargs)
        self.validate_inputs_outputs(self.column_names, inputs_columns, outputs_columns)
        self._inputs_columns = inputs_columns
        self._outputs_columns = outputs_columns

    @property
    def inputs_columns(self):
        return self._inputs_columns

    @inputs_columns.setter
    def inputs_columns(self, columns_names: List[str]):
        self._inputs_columns = columns_names

    @property
    def outputs_columns(self):
        return self._outputs_columns

    @outputs_columns.setter
    def outputs_columns(self, columns_names: List[str]):
        self._outputs_columns = columns_names

    @staticmethod
    def validate_inputs_outputs(
        names: List[str], inputs: List[str], outputs: List[str]
    ):
        """Validate the columns to be chosen as input and output.

        The method considers those that already exist in the dataset.

        Args:
            names (list): dataset column names
            inputs (list): list of names to be input columns
            outputs(list): list of names to be output columns.
        """
        if len(inputs) + len(outputs) > len(names):
            raise ValueError("inputs and outputs cannot have more elements than names")
            # Validate that inputs and outputs only contain elements that exist in names
        if not set(names).issuperset(set(inputs + outputs)):
            raise ValueError(
                "inputs and outputs can only contain elements that exist in names"
            )
            # Validate that the union of inputs and outputs is equal to names
        if set(inputs + outputs) != set(names):
            raise ValueError("the union of inputs and outputs must be equal to names")

    def cast(self, *args, **kwargs):
        """Override of the cast method to leave it in datasetdashai format.

        Returns
        -------
            DatasetDashAI: DatasetDashAI after cast.
        """
        ds = super().cast(*args, **kwargs)
        return DatasetDashAI(ds._data, self.inputs_columns, self.outputs_columns)

    def save_to_disk(self, dataset_path: str):
        """Override of the save to disk method to save datasetdashai info in json file.

        Parameters
        ----------
        dataset_path : str
            Path where the datasetdashai will be stored.
        """
        super().save_to_disk(dataset_path)
        with open(
            os.path.join(dataset_path, "dataset_dashai_info.json"),
            "w",
            encoding="utf-8",
        ) as dashai_info_file:
            data_dashai = {
                "inputs_columns": self.inputs_columns,
                "outputs_columns": self.outputs_columns,
            }
            json.dump(data_dashai, dashai_info_file, indent=2, sort_keys=True)

    @staticmethod
    def load_from_disk(dataset_path: str):
        """Load a dashai dataset from disk.

        Args:
            dataset_path (str): path where the datasetdashai will be stored
        Returns:
            DatasetDashAI: DatasetDashAI loaded from disk.
        """
        dataset = load_from_disk(dataset_path=dataset_path)
        with open(
            os.path.join(dataset_path, "dataset_dashai_info.json"),
            "r",
            encoding="utf-8",
        ) as dashai_info_file:
            dataset_dashai_info = json.load(dashai_info_file)
        inputs_columns = dataset_dashai_info["inputs_columns"]
        outputs_columns = dataset_dashai_info["outputs_columns"]
        return DatasetDashAI(dataset._data, inputs_columns, outputs_columns)

    def change_columns_type(self, types: Dict[str, str]):
        """Change the type of some columns.

        Note: This method is temporary and will probably be removed in new versions.

        Args:
            types (dict): dictionary which has as keys the names of the columns to be
            changed and as values the new types
        Returns:
            DatasetDashAI: DatasetDashAI after type changes.
        """
        if not isinstance(types, dict):
            raise TypeError(f"types should be a dict, got {type(types)}")

        # Check if columns names exists
        columns = self.column_names

        for column in types:
            if column in columns:
                pass
            else:
                raise ValueError(f"Class column '{column}' does not exist in dataset.")
        # set columns types
        new_features = self.features.copy()
        for column in types:
            # ESTO ES TEMPORAL
            if types[column] == "Categorico":
                names = list(set(self[column]))
                new_features[column] = ClassLabel(names=names)
            elif types[column] == "Numerico":
                new_features[column] = Value("float32")
        dataset = self.cast(new_features)
        return dataset
