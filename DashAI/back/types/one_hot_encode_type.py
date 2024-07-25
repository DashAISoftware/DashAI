from dataclasses import dataclass, field
from typing import List

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


if __name__ == "__main__":
    categories = ["a", "b", "c"]
    categorical = Categorical(num_classes=len(categories), names=categories)
    example1 = OneHotEncodeType(categorical_feature=categorical, category=categories[0])

    print(example1)
    try:
        example2 = OneHotEncodeType()
    except ValueError:
        print("Exception raised correctly")
