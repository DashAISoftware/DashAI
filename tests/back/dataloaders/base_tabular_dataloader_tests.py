"""Tabular Dataloaders tests."""

import pathlib
from abc import abstractmethod
from typing import Any, Dict, Type

import pytest
from datasets import DatasetDict
from datasets.builder import DatasetGenerationError

from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset, split_dataset
from DashAI.back.dataloaders.classes.dataloader import BaseDataLoader
from tests.back.scratch import scratch_dir

# TODO: Test no header, empty file, bad split folder structure.


def _isclose(a: int, b: int, tol: int = 2) -> bool:
    return abs(a - b) <= tol


def _read_file_wrapper(dataset_path: pathlib.Path) -> str:
    file = str(dataset_path)

    return file


class BaseTabularDataLoaderTester:
    @property
    @abstractmethod
    def dataloader_cls(self) -> Type[BaseDataLoader]:
        """The class of the `BaseDataLoader` subclass to test"""
        raise NotImplementedError

    @property
    @abstractmethod
    def data_type_name(self) -> str:
        """
        The name of the data type (e.g., excel, csv, json) where the test datasets
        are stored.
        """
        raise NotImplementedError

    def _test_load_data_from_file(
        self,
        dataset_path: pathlib.Path,
        params: Dict[str, Any],
        nrows: int,
        ncols: int,
    ) -> None:
        """
        Tests the `load_data` method of a `BaseDataLoader` subclass by loading data from
        different file formats and verifying the loaded dataset structure.

        Parameters
        ----------
        dataset_path : str
            The path to the dataset file.
        params : Dict[str, Any]
            Additional parameters to pass to the `load_data` method.
        nrows : int
            Number of expected rows.
        ncols : int
            Number of expected columns.
        """
        dataloder_instance = self.dataloader_cls()

        # open the dataset
        file = _read_file_wrapper(dataset_path)

        # load data
        dataset = dataloder_instance.load_data(
            filepath_or_buffer=file,
            temp_path=scratch_dir("dataloaders"),
            params=params,
        )

        # check if the dataset is a dataset dict and its correctly loaded.
        assert isinstance(dataset, DashAIDataset)
        assert dataset.num_rows == nrows
        assert dataset.num_columns == ncols

    def _test_load_data_from_zip(
        self,
        dataset_path: pathlib.Path,
        params: Dict[str, Any],
        train_nrows: int,
        test_nrows: int,
        val_nrows: int,
        ncols: int,
    ) -> None:
        """
        Tests the `load_data` method of a `BaseDataLoader` subclass by loading data
        from a zipped file and verifying that the loaded files structure (train, test
        and validation paths with each own files) is correct.

        Parameters
        ----------
        dataset_path : str
            The path to the zipped dataset file.
        params : Dict[str, Any]
            Additional parameters to pass to the `load_data` method.
        train_nrows : int
            Number of expected cols in the training set.
        test_nrows : int
            Number of expected cols in the test set.
        val_nrows : int
            Number of expected cols in the validatoin set.
        ncols : int
            Number of columns. It has to be the same in all splits.
        """

        # instance the dataloader
        dataloder_instance = self.dataloader_cls()

        # open the dataset

        dataset = dataloder_instance.load_data(
            filepath_or_buffer=str(dataset_path),
            temp_path=scratch_dir("dataloaders", "iris"),
            params=params,
        )
        dataset = split_dataset(dataset)

        # check each dataset of the datasetdict.
        assert isinstance(dataset, DatasetDict)

        assert "train" in dataset
        assert _isclose(dataset["train"].num_rows, train_nrows)
        assert dataset["train"].num_columns == ncols

        assert "test" in dataset
        assert _isclose(dataset["test"].num_rows, test_nrows)
        assert dataset["test"].num_columns == ncols

        assert "validation" in dataset
        assert _isclose(dataset["validation"].num_rows, val_nrows)
        assert dataset["validation"].num_columns == ncols

    def _test_dataloader_with_missing_required_params(
        self,
        dataset_path: pathlib.Path,
        params: Dict[str, Any],
        expected_error_msg: str,
    ) -> None:
        """
        Tests the `load_data` method of a `BaseDataLoader` subclass by providing invalid
        parameters and verifying that the expected error message is raised.

        Parameters
        ----------
        dataset_path : str
            The path to the dataset file.
        params : Dict[str, Any]
            Invalid parameters to pass to the `load_data` method.
        expected_error_msg : str
            The expected error message to be raised.

        """

        # instance the dataloader
        dataloder_instance = self.dataloader_cls()

        # open the dataset
        file = _read_file_wrapper(dataset_path)

        # try to load the dataloader with the wrong params, catch the exception and
        # compare the exception msg with the expected one.
        with pytest.raises(
            ValueError,
            match=expected_error_msg,
        ):
            dataloder_instance.load_data(
                filepath_or_buffer=file,
                temp_path=scratch_dir("dataloaders", "iris"),
                params=params,
            )

    def _test_dataloader_try_to_load_a_invalid_datasets(
        self,
        dataset_path: pathlib.Path,
        params: Dict[str, Any],
    ) -> None:
        """
        Tests the `load_data` method of a `BaseDataLoader` subclass by loading data
        from an invalid dataset path and verifying that the expected error is raised.

        Parameters
        ----------
        dataset_path : str
            The path to the invalid dataset file.
        params : Dict[str, Any]
            Additional parameters to pass to the `load_data` method.
        """

        # instance the dataloader
        dataloder_instance = self.dataloader_cls()

        # open the dataset
        file = _read_file_wrapper(dataset_path)

        # try to load the dataloader with the wrong params, catch the exception and
        # compare the exception msg with the expected one.
        with pytest.raises(
            DatasetGenerationError,
        ):
            dataloder_instance.load_data(
                filepath_or_buffer=file,
                temp_path=scratch_dir("dataloaders", "iris"),
                params=params,
            )
