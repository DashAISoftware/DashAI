from sklearn.preprocessing import SplineTransformer as SplineTransformerOperation

from DashAI.back.core.schema_fields import (
    schema_field,
    enum_field,
    int_field,
    bool_field,
)
from DashAI.back.core.schema_fields.base_schema import BaseSchema
from DashAI.back.converters.scikit_learn.sklearn_like_converter import (
    SklearnLikeConverter,
)


class SplineTransformerSchema(BaseSchema):
    n_knots: schema_field(
        int_field(ge=1),
        10,
        "Number of knots to place.",
    )  # type: ignore
    degree: schema_field(
        int_field(ge=1),
        3,
        "Degree of the spline basis.",
    )  # type: ignore
    knots: schema_field(
        enum_field(
            [
                "uniform",
                "quantile",
            ]
        ),  # {‘uniform’, ‘quantile’} or array-like of shape (n_knots, n_features)
        "uniform",
        "Set knot positions such that first knot <= features <= last knot.",
    )  # type: ignore
    extrapolation: schema_field(
        enum_field(["error", "constant", "linear", "continue", "periodic"]),
        "constant",
        "How to extrapolate beyond the boundaries.",
    )  # type: ignore
    include_bias: schema_field(
        bool_field(),
        True,
        "If True, then include a bias column, the feature in which all polynomial powers are zero (i.e. a column of ones - acts as an intercept term in a linear model).",
    )  # type: ignore
    order: schema_field(
        enum_field(["C", "F"]),
        "C",
        "Order of output array in the dense case. 'F' order is faster to compute, but may slow down subsequent estimators.",
    )  # type: ignore
    # Added in version 1.2
    # sparse_output: schema_field(
    #     bool_field(),
    #     False,
    #     "If True, the output will be a sparse matrix.",
    # )  # type: ignore


class SplineTransformer(SklearnLikeConverter, SplineTransformerOperation):
    """Scikit-learn's SplineTransformer wrapper for DashAI."""

    SCHEMA = SplineTransformerSchema
    DESCRIPTION = "Generate polynomial and interaction features."
