from dataclasses import dataclass

from datasets import ClassLabel

from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset
from DashAI.back.types.dashai_data_type import DashAIDataType


@dataclass
class Categorical(ClassLabel, DashAIDataType):
    """Wrapper for Hugging Face for representing categorical values.
    Internally the categorical values are integer numbers.
    There are 3 ways to define a `Categorical`,
    which correspond to the 3 arguments:

     * `num_classes`: Create 0 to (num_classes-1) labels.
     * `names`: List of label strings.
     * `names_file`: File containing the list of labels.

    Attributes
    ----------
    ClassLabel : _type_
        _description_

    num_classes : int, optional
        Number of classes. All labels must be < `num_classes`.
    names : list of str, optional
        String names for the integer classes.
        The order in which the names are provided is kept.
    names_file : str, optional
        Path to a file with names for the integer classes, one per line.
    """

    def __post_init__(self, num_classes, names_file):
        return super().__post_init__(num_classes, names_file)

    @staticmethod
    def from_classlabel(hf_feature: ClassLabel) -> "Categorical":
        """Creates a categorical data type instance with the information of
        the given Hugging Face feature `hf_feature`.

        Parameters
        ----------
        hf_feature : ClassLabel
            Hugging Face feature instance used to create a Categorical
            instance.

        Returns
        -------
        DashAIDataType
            _description_

        Raises
        ------
        TypeError
            Raises if `hf_feature` is not a ClassLabel instance.
        """
        if not isinstance(hf_feature, ClassLabel):
            raise TypeError("hf_feature should be a ClassLabel instance")

        return Categorical(hf_feature.names)


def class_encode_column(
    dataset: DashAIDataset, column: str, include_nulls: bool = False
) -> DashAIDataset:
    """Create a copy of the given dataset with the given column encoded to a
    categorical column with integer numbers.

    Parameters
    ----------
    dataset : DashAIDataset
        Dataset with the column to encode.
    column : str
        Name of the column to encode.
    include_nulls : bool, optional
        Whether to include null values in the encoding. If `True`,
        the null values will be encoded as the `"None"` class label.

    Returns
    -------
    DashAIDataset
        DashAI Dataset with the column encoded
    """
    if column not in dataset.column_names:
        raise ValueError(f"Column '{column}' is not in the dataset")
    dt = dataset.class_encode_column(column, include_nulls)
    feats = dt.features.copy()
    feats[column] = Categorical(feats[column].names)
    return DashAIDataset(dt.data).cast(feats)
