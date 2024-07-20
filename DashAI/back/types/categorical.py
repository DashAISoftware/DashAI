from dataclasses import dataclass

from datasets import ClassLabel


@dataclass
class Categorical(ClassLabel):
    """Wrapper for Hugging Face for representing categorical values.
    Internally the categorical values are integer numbers.
    There are 3 ways to define a `ClassLabel`,
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
