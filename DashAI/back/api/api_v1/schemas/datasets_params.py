from typing import Dict, List, Union

from pydantic import BaseModel


class DataLoaderParams(BaseModel):
    separator: Union[str, None] = ","
    data_key: Union[str, None] = "data"


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


class ColumnSpecItemParams(BaseModel):
    type: str
    dtype: str


class ColumnsSpecParams(BaseModel):
    columns: Dict[str, ColumnSpecItemParams]


class DatasetUpdateParams(BaseModel):
    name: str = None
    columns: Dict[str, ColumnSpecItemParams] = None
