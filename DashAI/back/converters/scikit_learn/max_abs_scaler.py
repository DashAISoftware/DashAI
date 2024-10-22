from sklearn.preprocessing import MaxAbsScaler as MaxAbsScalerOperation

from DashAI.back.core.schema_fields import (
    schema_field,
    bool_field,
)
from DashAI.back.core.schema_fields.base_schema import BaseSchema
from DashAI.back.converters.scikit_learn.sklearn_like_converter import (
    SklearnLikeConverter,
)


class MaxAbsScalerSchema(BaseSchema):
    copy: schema_field(
        bool_field(),
        True,
        "Set to False to perform inplace scaling.",
    )  # type: ignore


class MaxAbsScaler(SklearnLikeConverter, MaxAbsScalerOperation):
    """Scikit-learn's MaxAbsScaler wrapper for DashAI."""

    SCHEMA = MaxAbsScalerSchema
    DESCRIPTION = "Scale each feature by its maximum absolute value."
