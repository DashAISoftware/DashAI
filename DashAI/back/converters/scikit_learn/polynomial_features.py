from sklearn.preprocessing import PolynomialFeatures as PolynomialFeaturesOperation

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


class PolynomialFeaturesSchema(BaseSchema):
    degree: schema_field(
        int_field(ge=1),  # int or tuple (min_degree, max_degree)
        2,
        "The degree of the polynomial features.",
    )  # type: ignore
    interaction_only: schema_field(
        bool_field(),
        False,
        "If True, only interaction features are produced: features that are products of at most degree distinct input features (so not x[1] ** 2, x[0] * x[2] ** 3, etc.).",
    )  # type: ignore
    include_bias: schema_field(
        bool_field(),
        True,
        "If True (default), then include a bias column, the feature in which all polynomial powers are zero (i.e. a column of ones - acts as an intercept term in a linear model).",
    )  # type: ignore
    order: schema_field(
        enum_field(["C", "F"]),
        "C",
        "Order of output array in the dense case. 'F' order is faster to compute, but may slow down subsequent estimators.",
    )  # type: ignore


class PolynomialFeatures(SklearnLikeConverter, PolynomialFeaturesOperation):
    """Scikit-learn's PolynomialFeatures wrapper for DashAI."""

    SCHEMA = PolynomialFeaturesSchema
    DESCRIPTION = "Generate polynomial and interaction features."
