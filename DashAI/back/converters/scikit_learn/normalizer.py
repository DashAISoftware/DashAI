from sklearn.preprocessing import Normalizer as NormalizerOperation

from DashAI.back.core.schema_fields import (
    schema_field,
    enum_field,
    bool_field,
)
from DashAI.back.core.schema_fields.base_schema import BaseSchema
from DashAI.back.converters.scikit_learn.sklearn_like_converter import (
    SklearnLikeConverter,
)


class NormalizerSchema(BaseSchema):
    norm: schema_field(
        enum_field(["l1", "l2", "max"]),
        "l2",
        "The norm to use to normalize each non zero sample.",
    )  # type: ignore
    copy: schema_field(
        bool_field(),
        True,
        "Set to False to perform inplace row normalization.",
    )  # type: ignore


class Normalizer(SklearnLikeConverter, NormalizerOperation):
    """Scikit-learn's Normalizer wrapper for DashAI."""

    SCHEMA = NormalizerSchema
    DESCRIPTION = "Normalize samples individually to unit norm."
