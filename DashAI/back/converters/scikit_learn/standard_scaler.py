from sklearn.preprocessing import StandardScaler as StandardScalerOperation
from DashAI.back.core.schema_fields import bool_field, schema_field
from DashAI.back.core.schema_fields.base_schema import BaseSchema
from DashAI.back.converters.scikit_learn.sklearn_like_converter import (
    SklearnLikeConverter,
)


class StandardScalerSchema(BaseSchema):
    copy: schema_field(
        bool_field(),
        True,
        "If False, try to avoid a copy and do inplace scaling instead.",
    )  # type: ignore
    with_mean: schema_field(
        bool_field(),
        True,
        "If True, center the data before scaling.",
    )  # type: ignore
    with_std: schema_field(
        bool_field(),
        True,
        "If True, scale the data to unit variance (or equivalently, unit standard deviation).",
    )  # type: ignore


class StandardScaler(SklearnLikeConverter, StandardScalerOperation):
    """Scikit-learn's Standard Scaler wrapper for DashAI."""

    SCHEMA = StandardScalerSchema
    DESCRIPTION = (
        "Standardize features by removing the mean and scaling to unit variance."
    )
