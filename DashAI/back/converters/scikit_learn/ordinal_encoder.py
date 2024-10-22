from sklearn.preprocessing import OrdinalEncoder as OrdinalEncoderOperation

from DashAI.back.core.schema_fields import (
    schema_field,
    none_type,
    enum_field,
    union_type,
    int_field,
    float_field,
)
from DashAI.back.core.schema_fields.base_schema import BaseSchema
from DashAI.back.converters.scikit_learn.sklearn_like_converter import (
    SklearnLikeConverter,
)


class OrdinalEncoderSchema(BaseSchema):
    categories = schema_field(
        enum_field(
            [
                "auto",
            ]
        ),  # "auto" or a list of array-like
        "auto",
        "Categories (unique values) per feature.",
    )  # type: ignore
    # dtype = schema_field(
    #     enum_field(["int", "float"]), # number type
    #     "float",
    #     "Desired dtype of output.",
    # )  # type: ignore
    handle_unknown = schema_field(
        enum_field(["error", "use_encoded_value"]),
        "error",
        "Whether to raise an error or ignore if an unknown categorical feature is present during transform.",
    )  # type: ignore
    # unknown_value = schema_field(
    #     none_type(
    #         union_type(
    #             enum_field(["int", "np.nan"]), # int or np.nan
    #         )
    #     ),
    #     None,
    #     "The value to use for unknown categories.",
    # )  # type: ignore
    # encoded_missing_values = schema_field(
    #     enum_field(["int", "np.nan"]), # int or np.nan
    #     "np.nan",
    #     "Encoded value of missing categories.",
    # )  # type: ignore
    # Added in version 1.3
    # min_frequency = schema_field(
    #     none_type(union_type(int_field(ge=1), float_field(ge=0.0, le=1.0))),
    #     None,
    #     "Minimum frequency of a category to be considered as frequent.",
    # )  # type: ignore
    # Added in version 1.3
    # max_categories = schema_field(
    #     none_type(int_field(ge=1)),
    #     None,
    #     "Maximum number of categories to encode.",
    # )  # type: ignore


class OrdinalEncoder(SklearnLikeConverter, OrdinalEncoderOperation):
    """Scikit-learn's OrdinalEncoder wrapper for DashAI."""

    SCHEMA = OrdinalEncoderSchema
    DESCRIPTION = "Encode categorical features as an integer array."
