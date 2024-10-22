from sklearn.preprocessing import Binarizer as BinarizerOperation

from DashAI.back.core.schema_fields import (
    schema_field,
    bool_field,
    float_field,
)
from DashAI.back.core.schema_fields.base_schema import BaseSchema
from DashAI.back.converters.scikit_learn.sklearn_like_converter import (
    SklearnLikeConverter,
)


class BinarizerSchema(BaseSchema):
    threshold: schema_field(
        float_field(),
        0.0,
        "Feature values below or equal to this are replaced by 0, above it by 1.",
    )  # type: ignore
    copy: schema_field(
        bool_field(),
        True,
        "Set to False to perform inplace binarization.",
    )  # type: ignore


class Binarizer(SklearnLikeConverter, BinarizerOperation):
    """Scikit-learn's Binarizer wrapper for DashAI."""

    SCHEMA = BinarizerSchema
    DESCRIPTION = (
        "Binarize data (set feature values to 0 or 1) according to a threshold."
    )
