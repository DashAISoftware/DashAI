import json
import os
from typing import Dict, List, Literal, Union

import numpy as np
from datasets import ClassLabel, Dataset, DatasetDict, Value, load_from_disk


class DashAIDataset(Dataset):
    def __init__(
        self,
        table,
        inputs_columns: List[str],
        outputs_columns: List[str],
        *args,
        **kwargs,
    ):
        """DashAI wrapper for Hugging Face's Dataset with extra metadata.

        Parameters
        ----------
        table : Table
            arrow table from which the dataset will be created
        inputs_columns : List[str]
            list of names to be input columns
        outputs_columns : List[str]
            list of names to be output columns
        """
        super().__init__(table, *args, **kwargs)
        validate_inputs_outputs(self.column_names, inputs_columns, outputs_columns)
        self._inputs_columns = inputs_columns
        self._outputs_columns = outputs_columns

    @property
    def inputs_columns(self) -> List[str]:
        """Obtains the list of input columns.

        Returns
        -------
        List[str]
            List of input columns.
        """
        return self._inputs_columns

    @inputs_columns.setter
    def inputs_columns(self, columns_names: List[str]):
        """Set the input columns names.

        Parameters
        ----------
        columns_names : List[str]
            A list with the new input column names.
        """
        self._inputs_columns = columns_names

    @property
    def outputs_columns(self) -> List[str]:
        """Obtains the list of output columns.

        Returns
        -------
        List[str]
            List of output columns.
        """
        return self._outputs_columns

    @outputs_columns.setter
    def outputs_columns(self, columns_names: List[str]):
        """Set the output columns names.

        Parameters
        ----------
        columns_names : List[str]
            A list with the new output column names.
        """
        self._outputs_columns = columns_names

    def cast(self, *args, **kwargs):
        """Override of the cast method to leave it in DashAI dataset format.

        Returns
        -------
        DatasetDashAI
            Dataset after cast
        """
        ds = super().cast(*args, **kwargs)
        return DashAIDataset(ds._data, self.inputs_columns, self.outputs_columns)

    def save_to_disk(self, dataset_path: str):
        """Override save to disk method to save the dataset info in json file.

        Parameters
        ----------
        dataset_path : str
            path where the dataset will be stored
        """
        super().save_to_disk(dataset_path)
        with open(
            os.path.join(dataset_path, "dashai_dataset_metadata.json"),
            "w",
            encoding="utf-8",
        ) as dashai_info_file:
            data_dashai = {
                "inputs_columns": self.inputs_columns,
                "outputs_columns": self.outputs_columns,
            }
            json.dump(
                data_dashai,
                dashai_info_file,
                indent=2,
                sort_keys=True,
                ensure_ascii=False,
            )

    def change_columns_type(self, column_types: Dict[str, str]):
        """Change the type of some columns.

        Note: this is a temporal method, and it will probably will delete in the future.

        Parameters
        ----------
        column_types : Dict[str, str]
            dictionary whose keys are the names of the columns to be changed and the
            values the new types.

        Returns
        -------
        DashAIDataset
            The dataset after columns type changes.
        """
        if not isinstance(column_types, dict):
            raise TypeError(f"types should be a dict, got {type(column_types)}")

        for column in column_types:
            if column in self.column_names:
                pass
            else:
                raise ValueError(
                    f"Error while changing column types: column '{column}' does not "
                    "exist in dataset."
                )
        new_features = self.features.copy()
        for column in column_types:
            if column_types[column] == "Categorical":
                names = list(set(self[column]))
                new_features[column] = ClassLabel(names=names)
            elif column_types[column] == "Numerical":
                new_features[column] = Value("float32")
        dataset = self.cast(new_features)
        return dataset

    def sample(
        self,
        n: int = 1,
        method: Literal["head", "tail", "random"] = "head",
        seed: Union[int, None] = None,
    ) -> Dict[str, List]:
        """Return sample rows from dataset.

        Parameters
        ----------
        n : int
            number of samples to return.
        method: Literal[str]
            method for selecting samples. Possible values are: 'head' to
            select the first n samples, 'tail' to select the last n samples
            and 'random' to select n random samples.
        seed : int, optional
            seed for random number generator when using 'random' method.
        Returns
        -------
        Dict
            A dictionary with selected samples.
        """
        if n > len(self):
            raise ValueError(
                "Number of samples must be less than or equal to the length "
                f"of the dataset. Number of samples: {n}, "
                f"dataset length: {len(self)}"
            )

        if method == "random":
            rng = np.random.default_rng(seed=seed)
            indexes = rng.integers(low=0, high=(len(self) - 1), size=n)
            sample = self.select(indexes).to_dict()

        elif method == "head":
            sample = self[:n]

        elif method == "tail":
            sample = self[-n:]

        return sample


def validate_inputs_outputs(names: List[str], inputs: List[str], outputs: List[str]):
    """Validate the columns to be chosen as input and output.

    The algorithm considers those that already exist in the dataset.

    Parameters
    ----------
    names : List[str]
        Dataset column names.
    inputs : List[str]
        List of names to be input columns.
    outputs : List[str]
        List of names to be output columns.
    """
    if len(inputs) + len(outputs) > len(names):
        raise ValueError(
            "Inputs and outputs cannot have more elements than names. "
            f"Number of inputs: {len(inputs)}, "
            f"number of outputs: {len(outputs)}, "
            f"number of names: {len(names)}. "
        )
        # Validate that inputs and outputs only contain elements that exist in names
    if not set(names).issuperset(set(inputs + outputs)):
        raise ValueError(
            "Inputs and outputs can only contain elements that exist in names."
        )
        # Validate that the union of inputs and outputs is equal to names
    if set(inputs + outputs) != set(names):
        raise ValueError(
            "The union of the elements of inputs and outputs list must be equal to "
            "elements in the list of names."
        )


def load_dataset(datasetdict_path: str):
    """Load a datasetdict with dashaidatasets inside.

    Parameters
    ----------
    datasetdict_path : str
        path where the datasetdict is stored

    Returns
    -------
    DatasetDict
        The loaded datasetdict with dashaidatasets inside.
    """
    dataset = load_from_disk(dataset_path=datasetdict_path)
    for split in dataset:
        with open(
            os.path.join(datasetdict_path, f"{split}/dashai_dataset_metadata.json"),
            "r",
            encoding="utf-8",
        ) as dashai_info_file:
            dataset_dashai_info = json.load(dashai_info_file)
        inputs_columns = dataset_dashai_info["inputs_columns"]
        outputs_columns = dataset_dashai_info["outputs_columns"]
        dataset[split] = DashAIDataset(
            dataset[split].data, inputs_columns, outputs_columns
        )
    return dataset


def save_dataset(datasetdict: DatasetDict, dataset_path: str):
    """Save the datasetdict with dashaidatasets inside.

    Parameters
    ----------
    datasetdict : DatasetDict
        datasetdict to be saved

    datasetdict_path : str
        path where the datasetdict will be stored

    """
    splits = []
    for split in datasetdict:
        splits.append(split)
        datasetdict[split].save_to_disk(f"{dataset_path}/{split}")
    with open(
        os.path.join(dataset_path, "dataset_dict.json"),
        "w",
        encoding="utf-8",
    ) as datasetdict_info_file:
        data = {"splits": splits}
        json.dump(
            data,
            datasetdict_info_file,
            indent=2,
            sort_keys=True,
            ensure_ascii=False,
        )
