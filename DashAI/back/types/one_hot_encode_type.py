from copy import deepcopy
from dataclasses import dataclass, field
from typing import List

import numpy as np
from datasets import ClassLabel

from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset
from DashAI.back.types.categorical import Categorical


@dataclass
class OneHotEncodeType(Categorical):
    """Dataclass used to represent the type of a single one hot encoding
    column. It contains the original categorical feature corresponding
    to the label encoding and the category that the column represents.

    Attributes
    ----------
    categorical_feature : Categorical
        The categorical feature that contains the labels of the corresponding
        label encoding.
    category : str
        The category that the column represents in the label encoding.

    Raises:
        ValueError: _description_
        ValueError: _description_

    Returns:
        _type_: _description_
    """

    categorical_feature: Categorical = None
    category: str = None
    num_classes: int = field(default=2, init=False)
    names: List[str] = field(default=None, init=False)
    names_file: str = field(default=None, init=False)

    def __post_init__(self):
        if self.categorical_feature is None:
            raise ValueError("Original categorical feature is missing")
        if self.category is None:
            raise ValueError("Category is missing")
        return super().__post_init__(self.num_classes, self.names_file)


def one_hot_encode_column(dataset: DashAIDataset, column: str) -> DashAIDataset:
    """Create a copy with the given dataset with the given categorical column
    encoded to one hot encoding.

    Parameters
    ----------
    column : str
        Column to encode. It must be a categorical column.
    delete_original_column : bool, optional
        whether the original column is deleted, by default True
    """
    if column not in dataset.column_names:
        raise ValueError(f"Column '{column}' is not in the dataset.")
    if not isinstance(dataset.features[column], ClassLabel):
        raise ValueError("Only categorical columns can be one hot encoded.")

    categorical_feat: ClassLabel = dataset.features[column]
    categories = categorical_feat.names
    dt = deepcopy(dataset)
    column_categories_dict = {}

    # Add a column full of zeros for every category
    for category in categories:
        column_data = np.zeros(dt.num_rows, dtype=np.int64)
        column_name = f"{column}_{category}"
        column_categories_dict[column_name] = category
        dt = dt.add_column(column_name, column_data)

    def one_hot_encode(example):
        col_name = f"{column}_{categories[example[column]]}"
        example[col_name] = 1
        return example

    # Hugging Face dataset with one hot encoding
    dt = dt.map(one_hot_encode).remove_columns(column)

    # Add one hot encoding type and delete original column in features dict
    features = dataset.features.copy()
    del features[column]
    for col, cat in column_categories_dict.items():
        features[col] = OneHotEncodeType(
            categorical_feature=categorical_feat, category=cat
        )
    # DashAI dataset with one hot encoding
    dt = DashAIDataset(dt.data).cast(features)
    return dt
