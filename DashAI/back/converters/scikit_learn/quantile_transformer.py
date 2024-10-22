from sklearn.preprocessing import QuantileTransformer as QuantileTransformerOperation

from DashAI.back.core.schema_fields import (
    schema_field,
    none_type,
    enum_field,
    int_field,
    bool_field,
)
from DashAI.back.core.schema_fields.base_schema import BaseSchema
from DashAI.back.converters.scikit_learn.sklearn_like_converter import (
    SklearnLikeConverter,
)


class QuantileTransformerSchema(BaseSchema):
    n_quantiles: schema_field(
        int_field(ge=1),
        1000,  # default=1000 or n_samples
        "Number of quantiles to be computed. It corresponds to the number of landmarks used to discretize the cumulative distribution function.",
    )  # type: ignore
    output_distribution: schema_field(
        enum_field(["uniform", "normal"]),
        "uniform",
        "Marginal distribution for the transformed data. The choices are 'uniform' (default) or 'normal'.",
    )  # type: ignore
    ignore_implicit_zeros: schema_field(
        bool_field(),
        False,
        "Only applies to sparse matrices. If True, the sparse entries of the matrix are mapped as if they were explicit zeros.",
    )  # type: ignore
    # Added in version 1.5
    # subsample: schema_field(
    #     none_type(int_field(ge=1)),
    #     1e4,
    #     "Maximum number of samples used to estimate the quantiles for computational efficiency. Note that the subsampling procedure may differ for value-identical sparse and dense matrices.",
    # )  # type: ignore
    random_state: schema_field(
        none_type(int_field()),  # int, RandomState instance or None
        None,
        "Determines random number generation for subsampling. Pass an int for reproducible results across multiple function calls.",
    )  # type: ignore
    copy: schema_field(
        bool_field(),
        True,
        "Set to False to perform inplace transformation and avoid a copy (if the input is already a numpy array).",
    )  # type: ignore


class QuantileTransformer(SklearnLikeConverter, QuantileTransformerOperation):
    """Scikit-learn's QuantileTransformer wrapper for DashAI."""

    SCHEMA = QuantileTransformerSchema
    DESCRIPTION = "Transform features using quantiles information."
