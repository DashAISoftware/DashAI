from pydantic import BaseModel
from typing import Optional

class DataLoaderParams(BaseModel):
    separator : Optional[str]
    # add other params of dataloaders

class SplitParams(BaseModel):
    test_size : float = 0.1
    val_size  : float = 0.1
    seed      : int = None
    shuffle   : bool = True
    stratify  : bool = False

class DatasetParams(BaseModel):
    task_name    : str
    data_loader  : str
    dataset_name : str
    class_index  : int = -1
    folder_split : bool = False
    splits       : SplitParams
    dataloader_params : DataLoaderParams