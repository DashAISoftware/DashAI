from typing import Literal, Optional

from pydantic import BaseModel, Field


class DecisionTreeClassifier(BaseModel):
    criterion: Literal["gini", "entropy", "log_loss"] = Field(
        title="Criterion",
        description="""The criterion parameter is the function to measure the
        quality of a split. Possible values: gini, entropy or log_loss""",
    )
    max_depth: Optional[int] = Field(
        title="Max Depth",
        description="""The max_depth parameter is the maximum depth of the tree.
        If None, then nodes are expanded until all leaves are pure or until all leaves
        contain less than min_samples_split samples.""",
        ge=1,
    )
    min_samples_split: int = Field(
        title="Min Samples Split",
        description="""
        The min_samples_split parameter is the minimum number of samples required
        to split an internal node.""",
        ge=1,
    )
    min_samples_leaf: int = Field(
        title="Min Samples Leaf",
        description="""
        The min_samples_leaf parameter is the minimum number of samples
        required to be at a leaf node.""",
        ge=1,
    )
    max_features: Optional[Literal["auto", "sqrt", "log2"]] = Field(
        title="Max Features",
        description="""
        The max_features parameter is the number of features to consider
        when looking for the best split. The max_features parameter should be one of
        auto, sqrt, log2 or None.""",
    )
