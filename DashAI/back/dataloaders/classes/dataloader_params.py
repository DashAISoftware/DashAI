from typing import Optional, Union

from pydantic import BaseModel


class DataLoaderParams(BaseModel):
    separator: Optional[str] = ","
    data_key: Optional[str] = "data"
    # add other params of dataloaders


class SplitParams(BaseModel):
    train_size: float = 0.8
    test_size: float = 0.1
    val_size: float = 0.1
    seed: int = None
    shuffle: bool = True
    stratify: bool = False


class DatasetParams(BaseModel):
    task_name: str
    dataloader: str
    dataset_name: str
    class_column: Union[int, str] = -1
    splits_in_folders: bool = False
    splits: SplitParams
    dataloader_params: DataLoaderParams


""" Model's examples in a string,
    to test upload of a dataset

# --- Model for CSV Example ---
{
  "task_name": "NumericClassificationTask",
  "dataloader": "CSVDataLoader",
  "dataset_name": "example_csv",
  "class_column": -1,
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
    "separator": ","
  }
}
# --- Model for JSON example ---
{
  "task_name": "NumericClassificationTask",
  "dataloader": "JSONDataLoader",
  "dataset_name": "example_json",
  "class_column": "class",
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
