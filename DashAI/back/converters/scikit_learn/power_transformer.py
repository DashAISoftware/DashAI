from sklearn.preprocessing import PowerTransformer as PowerTransformerOperation

from DashAI.back.core.schema_fields import (
    schema_field,
    enum_field,
    bool_field,
)
from DashAI.back.core.schema_fields.base_schema import BaseSchema
from DashAI.back.converters.scikit_learn.sklearn_like_converter import (
    SklearnLikeConverter,
)


class PowerTransformerSchema(BaseSchema):
    method: schema_field(
        enum_field(["box-cox", "yeo-johnson"]),
        "yeo-johnson",
        "The power transform method. Box-Cox requires input data to be strictly positive, while Yeo-Johnson supports both positive or negative data.",
    )  # type: ignore
    standardize: schema_field(
        bool_field(),
        True,
        "Set to True to apply zero-mean, unit-variance normalization to the transformed output.",
    )  # type: ignore
    copy: schema_field(
        bool_field,
        True,
        "Set to False to perform inplace power transformation.",
    )  # type: ignore


class PowerTransformer(SklearnLikeConverter, PowerTransformerOperation):
    """Scikit-learn's PowerTransformer wrapper for DashAI."""

    SCHEMA = PowerTransformerSchema
    DESCRIPTION = "Apply a power transform featurewise to make data more Gaussian-like."
