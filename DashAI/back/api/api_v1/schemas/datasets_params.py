from typing import Dict, List, Union

from pydantic import BaseModel, ConfigDict


class SplitParams(BaseModel):
    train_size: float = 0.8
    test_size: float = 0.1
    val_size: float = 0.1


class MoreOptionsParams(BaseModel):
    shuffle: bool = True
    seed: int = 0
    statify: bool = False


class DatasetParams(BaseModel):
    model_config = ConfigDict(extra="allow")

    dataloader: str
    name: str
    splits_in_folders: bool = False
    splits: SplitParams
    more_options: MoreOptionsParams


class ColumnSpecItemParams(BaseModel):
    type: str
    dtype: str


class ColumnsSpecParams(BaseModel):
    columns: Dict[str, ColumnSpecItemParams]


class ConverterParams(BaseModel):
    params: Dict[str, Union[str, int, float, bool]]
    scope: Dict[str, List[int]] = None


class DatasetUpdateParams(BaseModel):
    name: str = None
    columns: Dict[str, ColumnSpecItemParams] = None
    converters: Dict[str, ConverterParams] = None
