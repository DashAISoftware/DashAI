from sklearn.preprocessing import OneHotEncoder as OneHotEncoderOperation

from DashAI.back.core.schema_fields import (
    schema_field,
    none_type,
    enum_field,
    union_type,
    bool_field,
    int_field,
    float_field,
)
from DashAI.back.core.schema_fields.base_schema import BaseSchema
from DashAI.back.converters.scikit_learn.sklearn_like_converter import (
    SklearnLikeConverter,
)


class OneHotEncoderSchema(BaseSchema):
    # categories = schema_field(
    #     list, # ‘auto’ or a list of array-like
    #     None,
    #     "The categories of each feature.",
    # )  # type: ignore
    # array-like of shape (n_features,)
    drop = schema_field(
        none_type(
            enum_field(["first", "if_binary"])
        ),  # {‘first’, ‘if_binary’} or an array-like of shape (n_features,)
        None,
        "Specifies a methodology to use to drop one of the categories per feature.",
    )  # type: ignore
    sparse_output = schema_field(
        bool_field(),
        True,
        "Whether the output should be a sparse matrix or dense array.",
    )  # type: ignore
    # dtype = schema_field(
    #     enum_field(["int", "np.float32", "np.float64"]), # number type
    #     "np.float64",
    #     "Desired dtype of output.",
    # )  # type: ignore
    handle_unknown = schema_field(
        enum_field(["error", "ignore", "infrequent_if_exist"]),
        "error",
        "Whether to raise an error or ignore if an unknown categorical feature is present during transform.",
    )  # type: ignore
    min_frequency = schema_field(
        none_type(union_type(int_field(ge=0), float_field(ge=0.0, le=1.0))),
        None,
        "Minimum frequency of a category to be considered as frequent.",
    )  # type: ignore
    max_categories = schema_field(
        none_type(int_field(ge=1)),
        None,
        "Maximum number of categories to encode.",
    )  # type: ignore
    # Added in version 1.3
    # feature_name_combiner = schema_field(
    #     enum_field(
    #         [
    #             "concat",
    #         ]
    #     ),  # “concat” or callable
    #     "concat",
    #     "Method used to combine feature names.",
    # )  # type: ignore


class OneHotEncoder(SklearnLikeConverter, OneHotEncoderOperation):
    """Scikit-learn's OneHotEncoder wrapper for DashAI."""

    SCHEMA = OneHotEncoderSchema
    DESCRIPTION = "Encode categorical integer features as a one-hot numeric array."
