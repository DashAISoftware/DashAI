from sklearn.preprocessing import RobustScaler as RobustScalerOperation

from DashAI.back.core.schema_fields import (
    schema_field,
    bool_field,
)
from DashAI.back.core.schema_fields.base_schema import BaseSchema
from DashAI.back.converters.scikit_learn.sklearn_like_converter import (
    SklearnLikeConverter,
)


class RobustScalerSchema(BaseSchema):
    with_centering: schema_field(
        bool_field(),
        True,
        "If True, center the data before scaling.",
    )  # type: ignore
    with_scaling: schema_field(
        bool_field(),
        True,
        "If True, scale the data to the IQR.",
    )  # type: ignore
    # quantile_range: schema_field(
    #     float, # tuple (q_min, q_max), 0.0 < q_min < q_max < 100.0
    #     25.0,
    #     "The IQR range used to scale the data.",
    # )  # type: ignore
    copy: schema_field(
        bool_field(),
        True,
        "Set to False to perform inplace scaling.",
    )  # type: ignore
    unit_variance: schema_field(
        bool_field(),
        False,
        "If True, scale the data to unit variance.",
    )  # type: ignore


class RobustScaler(SklearnLikeConverter, RobustScalerOperation):
    """Scikit-learn's RobustScaler wrapper for DashAI."""

    SCHEMA = RobustScalerSchema
    DESCRIPTION = "Scale features using statistics that are robust to outliers."
