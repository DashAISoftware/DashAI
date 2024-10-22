from sklearn.preprocessing import KBinsDiscretizer as KBinsDiscretizerOperation

from DashAI.back.core.schema_fields import (
    schema_field,
    none_type,
    enum_field,
    int_field,
)
from DashAI.back.core.schema_fields.base_schema import BaseSchema
from DashAI.back.converters.scikit_learn.sklearn_like_converter import (
    SklearnLikeConverter,
)


class KBinsDiscretizerSchema(BaseSchema):
    n_bins: schema_field(
        int_field(ge=2),  # int or array-like of shape (n_features,)
        5,
        "The number of bins to produce.",
    )  # type: ignore
    encode: schema_field(
        enum_field(["onehot", "onehot-dense", "ordinal"]),
        "onehot",
        "Method used to encode the transformed result.",
    )  # type: ignore
    strategy: schema_field(
        enum_field(["uniform", "quantile", "kmeans"]),
        "quantile",
        "Strategy used to define the widths of the bins.",
    )  # type: ignore
    # dtype: schema_field(
    #     none_type(enum_field(["np.float32", "np.float64"])), # {np.float32, np.float64}
    #     None,
    #     "The desired data-type for the output. If None, output dtype is consistent with input dtype.",
    # )  # type: ignore
    sub_sample: schema_field(
        none_type(int_field(gt=0)),
        None, # Changed in versions 1.3 and 1.5
        "Maximum number of samples used to estimate the quantiles for computing the bins.",
    )  # type: ignore
    random_state: schema_field(
        none_type(int_field()),  # int, RandomState instance or None
        None,
        "Determines random number generation for subsampling. Pass an int for reproducible results across multiple function calls.",
    )  # type: ignore


class KBinsDiscretizer(SklearnLikeConverter, KBinsDiscretizerOperation):
    """Scikit-learn's KBinsDiscretizer wrapper for DashAI."""

    SCHEMA = KBinsDiscretizerSchema
    DESCRIPTION = "Bin continuous data into intervals."
