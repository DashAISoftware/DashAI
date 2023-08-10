from typing import List, Union

from pydantic import BaseModel


class DataLoaderParams(BaseModel):
    separator: Union[str, None] = ","
    data_key: Union[str, None] = "data"
    # add other params of dataloaders


class SplitParams(BaseModel):
    train_size: float = 0.8
    test_size: float = 0.1
    val_size: float = 0.1
    seed: int = None
    shuffle: bool = True
    stratify: bool = False


class DatasetParams(BaseModel):
    dataloader: str
    dataset_name: str
    outputs_columns: List[str] = []
    splits_in_folders: bool = False
    splits: SplitParams
    dataloader_params: DataLoaderParams


""" Model's examples in a string,
    to test upload of a dataset

# --- Model for CSV Example ---
{
  "dataloader": "CSVDataLoader",
  "dataset_name": "example_csv",
  "outputs_columns": [],
  "splits_in_folders": false,
  "splits": {
    "train_size": 0.8,
    "test_size": 0.1,
    "val_size": 0.1,
    "seed": 42,
    "shuffle": true,
    "stratify": false
  },
  "dataloader_params": {
    "separator": ","
  }
}
# --- Model for JSON example ---
{
  "dataloader": "JSONDataLoader",
  "dataset_name": "example_json",
  "outputs_columns": [],
  "splits_in_folders": false,
  "splits": {
    "train_size": 0.8,
    "test_size": 0.1,
    "val_size": 0.1,
    "seed": null,
    "shuffle": true,
    "stratify": false
  },
  "dataloader_params": {
    "data_key": "data"
  }
}
"""
