from typing import Optional

from pydantic import BaseModel


class DataLoaderParams(BaseModel):
    separator: Optional[str] = ","
    # add other params of dataloaders


class SplitParams(BaseModel):
    test_size: float = 0.1
    val_size: float = 0.1
    seed: int = None
    shuffle: bool = True
    stratify: bool = False


class DatasetParams(BaseModel):
    task_name: str
    data_loader: str
    dataset_name: str
    class_index: int = -1
    folder_split: bool = False
    splits: SplitParams
    dataloader_params: DataLoaderParams


"""
# --- Model JSON Example ---

{
  "task_name": "NumericClassificationTask",
  "data_loader": "CSVDataLoader",
  "dataset_name": "example",
  "class_index": -1,
  "folder_split": false,
  "splits": {
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

"""
