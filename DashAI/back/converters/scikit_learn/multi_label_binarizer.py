from sklearn.preprocessing import MultiLabelBinarizer as MultiLabelBinarizerOperation

from DashAI.back.core.schema_fields import (
    schema_field,
    bool_field,
)
from DashAI.back.core.schema_fields.base_schema import BaseSchema
from DashAI.back.converters.scikit_learn.sklearn_like_converter import (
    SklearnLikeConverter,
)


class MultiLabelBinarizerSchema(BaseSchema):
    # classes: schema_field(
    #     list, # array-like of shape (n_features,)
    #     [],
    #     "Classes that will be binarized.",
    # )  # type: ignore
    sparse_output: schema_field(
        bool_field(),
        False,
        "True if the returned array from transform is desired to be in sparse CSR format.",
    )  # type: ignore


class MultiLabelBinarizer(SklearnLikeConverter, MultiLabelBinarizerOperation):
    """Scikit-learn's MultiLabelBinarizer wrapper for DashAI."""

    SCHEMA = MultiLabelBinarizerSchema
    DESCRIPTION = "Transform between iterable of iterables and a multilabel format."
